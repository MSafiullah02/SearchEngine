import numpy as np
from pathlib import Path
import os
import random

BASE_DIR = Path(__file__).resolve().parent.parent
EMBEDDINGS_PATH = BASE_DIR / "embeddings" / "wiki_giga_2024_100_MFT20_vectors_seed_2024_alpha_0.75_eta_0.05.050_combined.txt"

MAX_CANDIDATES = 20_000   # HARD CAP for RAM + speed
CACHE_LIMIT = 50_000     # prevent cache explosion


class SemanticSearchEngine:
    def __init__(self):
        self.embeddings = {}        # word -> vector
        self.word_norms = {}        # word -> norm
        self.loaded = False
        self.similar_words_cache = {}
        self.embedding_dim = 100

    def load_embeddings(self):
        """Load embeddings safely (skip bad lines, RAM-efficient)"""
        if self.loaded:
            return

        if not os.path.exists(EMBEDDINGS_PATH):
            print(f"Embeddings not found at {EMBEDDINGS_PATH}")
            self.loaded = False
            return

        print("[v1] Loading semantic embeddings (RAM-safe mode)...")
        self.embeddings = {}
        self.word_norms = {}

        with open(EMBEDDINGS_PATH, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split()
                if len(parts) != self.embedding_dim + 1:
                    print(f"[v1] Skipping line {line_num}: wrong dimension")
                    continue
                word = parts[0]
                try:
                    vec = np.array(parts[1:], dtype='float32')
                except ValueError:
                    print(f"[v1] Skipping line {line_num}: could not convert to float")
                    continue
                norm = np.linalg.norm(vec)
                if norm == 0:
                    continue
                self.embeddings[word] = vec
                self.word_norms[word] = norm

        self.loaded = True
        print(f"[v1] Loaded {len(self.embeddings)} embeddings")

    def cosine_similarity(self, v1, v2, n1, n2):
        return np.dot(v1, v2) / (n1 * n2)

    def find_similar_words(self, word, top_k=3, threshold=0.7):
        if not self.loaded:
            self.load_embeddings()
        if word not in self.embeddings:
            return []

        cache_key = (word, top_k, threshold)
        if cache_key in self.similar_words_cache:
            return self.similar_words_cache[cache_key]

        query_vec = self.embeddings[word]
        query_norm = self.word_norms[word]

        results = []
        for w, vec in random.sample(list(self.embeddings.items()), min(MAX_CANDIDATES, len(self.embeddings))):
            if w == word:
                continue
            sim = self.cosine_similarity(query_vec, vec, query_norm, self.word_norms[w])
            if sim >= threshold:
                results.append((w, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]

        if len(self.similar_words_cache) < CACHE_LIMIT:
            self.similar_words_cache[cache_key] = results

        return results

    def expand_query(self, tokens, top_k=2, threshold=0.7):
        expanded = {}
        for token in tokens:
            sims = self.find_similar_words(token, top_k, threshold)
            if sims:
                expanded[token] = sims
        return expanded


_semantic_engine = None

def get_semantic_engine():
    global _semantic_engine
    if _semantic_engine is None:
        _semantic_engine = SemanticSearchEngine()
        _semantic_engine.load_embeddings()
    return _semantic_engine

