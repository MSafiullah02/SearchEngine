import numpy as np
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
EMBEDDINGS_PATH = BASE_DIR / "embeddings" / "wiki_giga_2024_100_MFT20_vectors_seed_2024_alpha_0.75_eta_0.05.050_combined.txt"

class SemanticSearchEngine:
    def __init__(self):
        self.embeddings = {}
        self.embedding_dim = 100
        self.loaded = False
        self.word_norms = {}  # Pre-computed norms for each word
        self.similar_words_cache = {}  # Cache for frequently searched words
        self.embedding_matrix = None  # Matrix of all embeddings for vectorized operations
        self.word_list = None  # List of words corresponding to matrix rows
        
    def load_embeddings(self):
        """Load pre-trained GloVe embeddings"""
        if self.loaded:
            return
            
        if not os.path.exists(EMBEDDINGS_PATH):
            print(f"Warning: GloVe embeddings not found at {EMBEDDINGS_PATH}")
            print("Semantic search will be disabled. Download 2024 GloVe embeddings from:")
            print("https://nlp.stanford.edu/data/glove.2024.wikigiga.100d.zip")
            print(f"Extract and place wiki_giga_2024_100_MFT20_vectors_seed_2024_alpha_0.75_eta_0.05.050_combined.txt in {BASE_DIR / 'embeddings'}/")
            return
            
        print("Loading 2024 GloVe embeddings...")
        embeddings_list = []
        words_list = []
        
        with open(EMBEDDINGS_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                values = line.strip().split()
                word = values[0]
                try:
                    vector = np.array(values[1:], dtype='float32')
                    if len(vector) == self.embedding_dim:
                        self.embeddings[word] = vector
                        embeddings_list.append(vector)
                        words_list.append(word)
                        self.word_norms[word] = np.linalg.norm(vector)
                except ValueError:
                    continue
        
        if embeddings_list:
            self.embedding_matrix = np.array(embeddings_list, dtype='float32')
            self.word_list = words_list
        
        self.loaded = True
        print(f"Loaded {len(self.embeddings)} word embeddings")
    
    def get_embedding(self, word):
        """Get embedding vector for a word"""
        return self.embeddings.get(word)
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_similar_words(self, word, top_k=5, threshold=0.6):
        """
        Find semantically similar words using cosine similarity with vectorized operations
        
        Args:
            word: The query word
            top_k: Number of similar words to return
            threshold: Minimum similarity threshold (0-1)
        
        Returns:
            List of (similar_word, similarity_score) tuples
        """
        if not self.loaded:
            self.load_embeddings()
            
        if not self.loaded or word not in self.embeddings:
            return []
        
        cache_key = f"{word}_{top_k}_{threshold}"
        if cache_key in self.similar_words_cache:
            return self.similar_words_cache[cache_key]
        
        word_vec = self.embeddings[word]
        word_norm = self.word_norms[word]
        
        if word_norm == 0:
            return []
        
        # Compute all dot products at once using matrix multiplication
        dot_products = np.dot(self.embedding_matrix, word_vec)
        
        # Get pre-computed norms for all words
        all_norms = np.array([self.word_norms[w] for w in self.word_list], dtype='float32')
        
        # Compute all similarities at once
        similarities = dot_products / (all_norms * word_norm + 1e-10)
        
        # Filter by threshold and get top_k
        valid_indices = np.where(similarities >= threshold)[0]
        
        if len(valid_indices) == 0:
            return []
        
        # Get top_k indices with highest similarity (excluding the word itself)
        top_indices = []
        for idx in valid_indices:
            if self.word_list[idx] != word:
                top_indices.append((idx, similarities[idx]))
        
        top_indices.sort(key=lambda x: x[1], reverse=True)
        top_indices = top_indices[:top_k]
        
        result = [(self.word_list[idx], float(sim)) for idx, sim in top_indices]
        
        self.similar_words_cache[cache_key] = result
        
        return result
    
    def expand_query(self, tokens, top_k=3, threshold=0.6):
        """
        Expand query tokens with semantically similar words
        
        Args:
            tokens: List of query tokens
            top_k: Number of similar words to add per token
            threshold: Minimum similarity threshold
        
        Returns:
            Dictionary mapping original tokens to similar tokens with weights
            Format: {token: [(similar_word, weight), ...]}
        """
        expanded = {}
        
        for token in tokens:
            similar = self.find_similar_words(token, top_k=top_k, threshold=threshold)
            if similar:
                expanded[token] = similar
        
        return expanded

# Global instance
_semantic_engine = None

def get_semantic_engine():
    """Get or create the global semantic search engine instance"""
    global _semantic_engine
    if _semantic_engine is None:
        _semantic_engine = SemanticSearchEngine()
        _semantic_engine.load_embeddings()
    return _semantic_engine

