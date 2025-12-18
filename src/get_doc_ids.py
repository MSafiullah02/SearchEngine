from src.tokenizer import tokenize
import re
from pathlib import Path
import numpy as np
import math

from src.semantic_search import get_semantic_engine

BASE_DIR = Path(__file__).resolve().parent.parent
LEXICON_DIR = BASE_DIR / "lexicon"
INVERTED_INDEX_DIR = BASE_DIR / "inverted_index"

BM25_K1 = 1.5  # Term frequency saturation parameter (standard value)
BM25_B = 0.75  # Document length normalization (standard value)

_doc_embeddings_cache = None
_doc_stats_cache = None


def load_doc_embeddings():
    """Load pre-computed document term embeddings."""
    global _doc_embeddings_cache
    if _doc_embeddings_cache is not None:
        return _doc_embeddings_cache

    embeddings_path = BASE_DIR / "doc_embeddings.npz"
    if not embeddings_path.exists():
        return None

    try:
        data = np.load(embeddings_path, allow_pickle=True)
        doc_embeddings = {}

        # Reconstruct the document embeddings dictionary
        doc_ids = set()
        for key in data.files:
            if key.endswith('_terms'):
                doc_id = key[:-6]  # Remove '_terms'
                doc_ids.add(doc_id)

        for doc_id in doc_ids:
            terms = data[f"{doc_id}_terms"]
            embeddings = data[f"{doc_id}_embeddings"]
            doc_embeddings[doc_id] = {term: emb for term, emb in zip(terms, embeddings)}

        _doc_embeddings_cache = doc_embeddings
        return doc_embeddings
    except Exception as e:
        print(f"Error loading document embeddings: {e}")
        return None


def load_doc_stats():
    """Load document statistics for BM25 scoring."""
    global _doc_stats_cache
    if _doc_stats_cache is not None:
        return _doc_stats_cache

    stats_path = BASE_DIR / "doc_stats.txt"
    if not stats_path.exists():
        return None

    try:
        stats = {}
        with open(stats_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    doc_id = parts[0]
                    doc_length = int(parts[1])
                    stats[doc_id] = {'length': doc_length}

        _doc_stats_cache = stats
        return stats
    except Exception as e:
        print(f"Error loading document stats: {e}")
        return None


def calculate_semantic_boost(query_tokens, doc_id, semantic_engine, doc_embeddings):
    """
    Calculate a semantic similarity boost for a document based on query-document term similarity.

    Returns a multiplier (1.0 = no boost, >1.0 = boost based on semantic similarity)
    """
    if not doc_embeddings or doc_id not in doc_embeddings:
        return 1.0

    doc_terms = doc_embeddings[doc_id]
    if not doc_terms:
        return 1.0

    # Calculate average maximum similarity between query terms and document terms
    similarities = []
    for query_token in query_tokens:
        if query_token not in semantic_engine.embeddings:
            continue

        query_emb = semantic_engine.embeddings[query_token]
        max_sim = 0.0

        # Find most similar term in document
        for doc_term, doc_emb in doc_terms.items():
            sim = semantic_engine.cosine_similarity(query_emb, doc_emb)
            max_sim = max(max_sim, sim)

        if max_sim > 0:
            similarities.append(max_sim)

    if not similarities:
        return 1.0

    # Average similarity as boost factor (scaled to 1.0-2.0 range)
    avg_similarity = np.mean(similarities)
    # Boost ranges from 1.0 (no similarity) to 2.0 (perfect similarity)
    boost = 1.0 + avg_similarity
    return boost


def get_doc_ids(text, use_semantic=True, semantic_weight=0.3):
    """
    Retrieve documents matching the query text with BM25 scoring and optional semantic search.

    Args:
        text: The search query
        use_semantic: Whether to use semantic search expansion and scoring
        semantic_weight: Weight for semantic expansion terms (0-1), standard is 0.3

    Returns:
        List of [doc_name, score] sorted by relevance
    """
    tokens = tokenize(text)
    if not tokens:
        return []

    semantic_engine = get_semantic_engine() if use_semantic else None
    doc_embeddings = load_doc_embeddings() if use_semantic and semantic_engine else None
    doc_stats = load_doc_stats()

    expanded_tokens = {}

    if use_semantic and semantic_engine and semantic_engine.loaded:
        expanded_tokens = semantic_engine.expand_query(tokens, top_k=3, threshold=0.65)

    all_tokens = list(tokens)  # Original tokens (will get full weight)
    semantic_terms = {}  # Track which terms are semantic expansions and their weights

    for original_token, similar_words in expanded_tokens.items():
        for similar_word, similarity in similar_words:
            similar_tokens = tokenize(similar_word)
            for sim_token in similar_tokens:
                if sim_token not in all_tokens:
                    all_tokens.append(sim_token)
                    semantic_terms[sim_token] = similarity * semantic_weight

    all_tokens.sort(key=lambda s: ord(s[0]) - ord('a') if s and 'a' <= s[0] <= 'z' else 26)

    term_ids = []
    term_weights = {}
    term_df = {}  # Document frequency for each term (for IDF calculation)
    file_id = 1
    data = {}

    def update_lexicon():
        data.clear()
        with open(LEXICON_DIR / f"lexicon{file_id}.txt", "r", encoding="utf-8") as f:
            for line in f:
                term, term_id = line.strip().split('\t')
                data[term] = int(term_id)

    update_lexicon()

    for token in all_tokens:
        if not token:
            continue

        if ord(token[0]) < ord('a') or ord(token[0]) > ord('z'):
            file_id = 27
            update_lexicon()
        elif ord(token[0]) - ord('a') != file_id - 1:
            file_id = ord(token[0]) - ord('a') + 1
            update_lexicon()

        term_id = data.get(token)
        if term_id is not None:
            term_ids.append(term_id)
            if token in semantic_terms:
                term_weights[term_id] = semantic_terms[token]
            else:
                term_weights[term_id] = 1.0

    term_ids.sort(key=lambda x: (x % 100, x))

    file_id = 0

    def update_inverted_index():
        data.clear()
        with open(INVERTED_INDEX_DIR / f"inverted_index{file_id}.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t', 1)
                term_id = int(parts[0])
                postings = []
                if len(parts) > 1:
                    for p in re.split(r'[\t ]+', parts[1]):
                        if ':' not in p:
                            continue
                        doc_name, count = p.split(':', 1)
                        postings.append([doc_name, int(count)])
                data[term_id] = postings

    update_inverted_index()

    term_postings = {}
    total_docs = 0

    for term_id in term_ids:
        if term_id % 100 != file_id:
            file_id = term_id % 100
            update_inverted_index()

        postings = data.get(term_id, [])
        term_postings[term_id] = postings
        term_df[term_id] = len(postings)
        if postings:
            total_docs = max(total_docs, len(postings) * 100)  # Estimate

    avg_doc_length = 1000  # Default estimate
    if doc_stats:
        total_length = sum(s['length'] for s in doc_stats.values())
        avg_doc_length = total_length / len(doc_stats) if doc_stats else 1000
        total_docs = len(doc_stats)

    doc_dict = {}

    for term_id, postings in term_postings.items():
        weight = term_weights.get(term_id, 1.0)
        df = term_df[term_id]

        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)

        for doc_name, tf in postings:
            doc_length = doc_stats.get(doc_name, {}).get('length', avg_doc_length) if doc_stats else avg_doc_length

            numerator = tf * (BM25_K1 + 1)
            denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * (doc_length / avg_doc_length))
            bm25_score = idf * (numerator / denominator) * weight

            doc_dict[doc_name] = doc_dict.get(doc_name, 0.0) + bm25_score

    if use_semantic and semantic_engine and semantic_engine.loaded and doc_embeddings:
        for doc_name in doc_dict:
            boost = calculate_semantic_boost(tokens, doc_name, semantic_engine, doc_embeddings)
            # Standard approach: multiply by boost factor (1.0 to 2.0)
            doc_dict[doc_name] *= boost

    doc_ids = [[name, count] for name, count in doc_dict.items()]
    doc_ids.sort(key=lambda x: x[1], reverse=True)

    return doc_ids
