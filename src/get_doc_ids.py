from src.tokenizer import tokenize
import re
from pathlib import Path

from src.semantic_search import get_semantic_engine

BASE_DIR = Path(__file__).resolve().parent.parent
LEXICON_DIR = BASE_DIR / "lexicon"
INVERTED_INDEX_DIR = BASE_DIR / "inverted_index"

def get_doc_ids(text, use_semantic=True, semantic_weight=0.3):
    """
    Retrieve documents matching the query text with optional semantic search.
    
    Args:
        text: The search query
        use_semantic: Whether to use semantic search expansion
        semantic_weight: Weight for semantic matches (0-1), where 1 is equal weight to exact matches
    
    Returns:
        List of [doc_name, score] sorted by relevance
    """
    tokens = tokenize(text)
    if not tokens:
        return []
    
    semantic_engine = get_semantic_engine() if use_semantic else None
    expanded_tokens = {}
    
    if use_semantic and semantic_engine and semantic_engine.loaded:
        expanded_tokens = semantic_engine.expand_query(tokens, top_k=3, threshold=0.65)
    
    all_tokens = list(tokens)  # Original tokens (will get full weight)
    semantic_terms = {}  # Track which terms are semantic expansions and their weights
    
    for original_token, similar_words in expanded_tokens.items():
        for similar_word, similarity in similar_words:
            # Tokenize the similar word to ensure it matches lexicon format
            similar_tokens = tokenize(similar_word)
            for sim_token in similar_tokens:
                if sim_token not in all_tokens:
                    all_tokens.append(sim_token)
                    # Store the weight for this semantic expansion
                    semantic_terms[sim_token] = similarity * semantic_weight
    
    # Sort tokens for lexicon lookup
    all_tokens.sort(key=lambda s: ord(s[0]) - ord('a') if s and 'a' <= s[0] <= 'z' else 26)
    
    term_ids = []
    term_weights = {}  # Track weights for each term_id
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
        
        # select the correct lexicon barrel
        if ord(token[0]) < ord('a') or ord(token[0]) > ord('z'):
            file_id = 27
            update_lexicon()
        elif ord(token[0]) - ord('a') != file_id - 1:
            file_id = ord(token[0]) - ord('a') + 1
            update_lexicon()
        
        # lookup term_id directly from the dictionary
        term_id = data.get(token)
        if term_id is not None:
            term_ids.append(term_id)
            if token in semantic_terms:
                term_weights[term_id] = semantic_terms[token]
            else:
                term_weights[term_id] = 1.0
    
    # sort term_ids by modulo 100 and then by value
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
    
    doc_dict = {}  # key: doc_name, value: weighted count
    
    for term_id in term_ids:
        # load the correct inverted index barrel if needed
        if term_id % 100 != file_id:
            file_id = term_id % 100
            update_inverted_index()
        
        # lookup postings directly from the dict
        postings = data.get(term_id, [])
        weight = term_weights.get(term_id, 1.0)
        
        for doc_name, count in postings:
            doc_dict[doc_name] = doc_dict.get(doc_name, 0.0) + (count * weight)
    
    # convert to combined list and sort by weighted count
    doc_ids = [[name, count] for name, count in doc_dict.items()]
    doc_ids.sort(key=lambda x: x[1], reverse=True)
    
    return doc_ids

