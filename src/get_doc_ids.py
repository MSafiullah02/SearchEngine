from src.tokenizer import tokenize
from pathlib import Path
import math
import os

from src.semantic_search import get_semantic_engine

BASE_DIR = Path(__file__).resolve().parent.parent
LEXICON_DIR = BASE_DIR / "lexicon"
INVERTED_INDEX_DIR = BASE_DIR / "inverted_index"

BM25_K1 = 1.5
BM25_B = 0.75

_lexicon_cache = {}
_total_docs = 100_000
_avg_doc_length = 1500


def _get_lexicon_barrel(file_id):
    if file_id in _lexicon_cache:
        return _lexicon_cache[file_id]

    data = {}
    path = LEXICON_DIR / f"lexicon{file_id}.txt"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                term, term_id = line.rstrip().split('\t')
                data[term] = int(term_id)

    _lexicon_cache[file_id] = data
    return data


def _load_postings(term_id):
    """
    Load postings ONLY for a single term_id
    """
    inv_id = term_id % 100
    path = INVERTED_INDEX_DIR / f"inverted_index{inv_id}.txt"

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line:
                continue

            if not line.startswith(str(term_id)):
                continue

            _, rest = line.rstrip().split('\t', 1)
            postings = []
            for p in rest.split():
                doc, tf = p.split(':')
                postings.append((doc, int(tf)))
            return postings

    return []


def get_doc_ids(text, use_semantic=True, semantic_weight=0.3):
    tokens = tokenize(text)
    if not tokens:
        return []

    # --- Semantic expansion (lightweight) ---
    semantic_terms = {}
    if use_semantic:
        engine = get_semantic_engine()
        if engine and engine.loaded:
            expanded = engine.expand_query(tokens, top_k=2, threshold=0.7)
            for _, sims in expanded.items():
                for word, sim in sims:
                    for t in tokenize(word):
                        semantic_terms[t] = sim * semantic_weight

    all_tokens = set(tokens) | set(semantic_terms.keys())

    # --- Resolve term IDs ---
    term_entries = []
    for token in all_tokens:
        if not token:
            continue

        if 'a' <= token[0] <= 'z':
            lex_id = ord(token[0]) - 96
        else:
            lex_id = 27

        lex = _get_lexicon_barrel(lex_id)
        term_id = lex.get(token)
        if term_id is not None:
            weight = semantic_terms.get(token, 1.0)
            term_entries.append((term_id, weight))

    if not term_entries:
        return []

    doc_scores = {}
    doc_len_cache = {}

    # --- Main scoring loop ---
    for term_id, q_weight in term_entries:
        postings = _load_postings(term_id)
        df = len(postings)
        if df == 0:
            continue

        idf = math.log(((_total_docs - df + 0.5) / (df + 0.5)) + 1)

        for doc, tf in postings:
            dl = doc_len_cache.get(doc, _avg_doc_length)
            doc_len_cache[doc] = dl  # single write

            denom = tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / _avg_doc_length)
            score = idf * (tf * (BM25_K1 + 1)) / denom

            doc_scores[doc] = doc_scores.get(doc, 0.0) + score * q_weight

    results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    return results

