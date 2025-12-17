from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
import sys
import os
import pickle

# Add src to path to import the modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.get_doc_ids import get_doc_ids

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
TEST_BATCH_DIR = BASE_DIR / "src" / "test_batch"
LEXICON_DIR = BASE_DIR / "lexicon"

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.word = None

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.word = word
    
    def search_prefix(self, prefix, limit=5):
        node = self.root
        prefix_lower = prefix.lower()
        
        # Navigate to the prefix node
        for char in prefix_lower:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Find all words with this prefix
        results = []
        self._dfs(node, results, limit)
        return results[:limit]
    
    def _dfs(self, node, results, limit):
        if len(results) >= limit:
            return
        if node.is_end and node.word:
            results.append(node.word)
        for child in node.children.values():
            self._dfs(child, results, limit)

autocomplete_trie = Trie()

def load_lexicon():
    """Load lexicon from text barrel files and populate the Trie"""
    try:
        print("[v0] Loading lexicon for autocomplete...")
        word_count = 0
        
        for i in range(1, 28):
            lexicon_file = LEXICON_DIR / f"lexicon{i}.txt"
            if lexicon_file.exists():
                with open(lexicon_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            # Format: term\tterm_id
                            parts = line.split('\t')
                            if parts:
                                term = parts[0]
                                autocomplete_trie.insert(term)
                                word_count += 1
        
        print(f"[v0] Loaded {word_count} words into autocomplete Trie")
    except Exception as e:
        print(f"[v0] Error loading lexicon: {e}")
        import traceback
        traceback.print_exc()

# Load lexicon on startup
load_lexicon()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    try:
        prefix = request.args.get('query', '').strip()
        
        if not prefix or len(prefix) < 2:
            return jsonify({'suggestions': []})
        
        # Get last word from the query for autocomplete
        words = prefix.split()
        last_word = words[-1] if words else prefix
        
        suggestions = autocomplete_trie.search_prefix(last_word, limit=5)
        
        # If we have multiple words, prepend the earlier words to suggestions
        if len(words) > 1:
            prefix_part = ' '.join(words[:-1]) + ' '
            suggestions = [prefix_part + sug for sug in suggestions]
        
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        print(f"[v0] Autocomplete error: {e}")
        return jsonify({'suggestions': []}), 500

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.json
        query = data.get('query', '')
        
        print(f"[v0] Received search query: {query}")
        print(f"[v0] Current directory: {os.getcwd()}")
        print(f"[v0] BASE_DIR: {BASE_DIR}")
        print(f"[v0] TEST_BATCH_DIR: {TEST_BATCH_DIR}")
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        print(f"[v0] Calling get_doc_ids with query: {query}")
        doc_results = get_doc_ids(query)
        
        print(f"[v0] get_doc_ids returned: {doc_results[:3] if doc_results else []}")
        print(f"[v0] Total results: {len(doc_results) if doc_results else 0}")
        
        results = []
        for doc_name, count in doc_results[:50]:  # Limit to top 50 results
            print(f"[v0] Processing doc: {doc_name} with score: {count}")
            
            # Try to load the JSON file
            json_path = TEST_BATCH_DIR / f"{doc_name}.json"
            if not json_path.exists():
                # Try with .xml.json extension for PMC files
                json_path = TEST_BATCH_DIR / f"{doc_name}.xml.json"
            
            print(f"[v0] Looking for JSON at: {json_path}")
            print(f"[v0] JSON exists: {json_path.exists()}")
            
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                    
                    paper_id = doc_data.get('paper_id', doc_name)
                    metadata = doc_data.get('metadata', {})
                    title = metadata.get('title', 'Untitled Document')
                    authors = metadata.get('authors', [])
                    
                    # Get author names
                    author_names = []
                    for author in authors[:3]:  # Limit to first 3 authors
                        first = author.get('first', '')
                        last = author.get('last', '')
                        if first and last:
                            author_names.append(f"{first} {last}")
                        elif last:
                            author_names.append(last)
                    
                    author_str = ', '.join(author_names)
                    if len(authors) > 3:
                        author_str += ', et al.'
                    
                    # Get abstract or first body text
                    abstract = ''
                    if 'abstract' in doc_data and doc_data['abstract']:
                        if isinstance(doc_data['abstract'], list) and len(doc_data['abstract']) > 0:
                            abstract = doc_data['abstract'][0].get('text', '')
                    
                    if not abstract and 'body_text' in doc_data and doc_data['body_text']:
                        if isinstance(doc_data['body_text'], list) and len(doc_data['body_text']) > 0:
                            abstract = doc_data['body_text'][0].get('text', '')[:300] + '...'
                    
                    url = doc_data.get('url', '')
                    if not url:
                        # Generate URL (for PMC papers, link to PubMed Central)
                        if paper_id.startswith('PMC'):
                            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{paper_id}/"
                        else:
                            # For non-PMC papers, try to use the paper_id as a DOI or direct link
                            # If it looks like a hash, construct a semantic scholar link
                            url = f"https://www.semanticscholar.org/paper/{paper_id}"
                    
                    score_value = float(count) if hasattr(count, 'item') else count
                    
                    results.append({
                        'id': paper_id,
                        'title': title or 'Untitled Document',
                        'authors': author_str or 'Unknown Authors',
                        'abstract': abstract,
                        'score': score_value,
                        'url': url,
                        'doc_name': doc_name
                    })
                    print(f"[v0] Successfully added result for {paper_id} with URL: {url}")
                except Exception as e:
                    print(f"[v0] Error loading {json_path}: {e}")
                    continue
            else:
                print(f"[v0] JSON file not found for {doc_name}")
        
        print(f"[v0] Returning {len(results)} formatted results")
        return jsonify({
            'results': results,
            'total': len(results),
            'query': query
        })
    
    except Exception as e:
        import traceback
        print(f"[v0] Search error: {e}")
        print(f"[v0] Full traceback:")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

