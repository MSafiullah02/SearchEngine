from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
import sys
import os
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from get_doc_ids import get_doc_ids
from document_indexer import DocumentIndexer

BASE_DIR = Path(__file__).resolve().parent
JSONS_DIR = BASE_DIR / "jsons"
LEXICON_DIR = BASE_DIR / "lexicon"

# ✅ Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# -----------------------------
# Autocomplete Trie
# -----------------------------
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
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
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
    """Load lexicon for autocomplete"""
    try:
        print("[v1] Loading lexicon for autocomplete...")
        word_count = 0
        for i in range(1, 28):
            lexicon_file = LEXICON_DIR / f"lexicon{i}.txt"
            if lexicon_file.exists():
                with open(lexicon_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            term = line.split('\t')[0]
                            autocomplete_trie.insert(term)
                            word_count += 1
        print(f"[v1] Loaded {word_count} words into autocomplete Trie")
    except Exception as e:
        print(f"[v1] Error loading lexicon: {e}")
        traceback.print_exc()

# Load lexicon once
load_lexicon()

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    index_path = BASE_DIR / "static" / "index.html"
    if index_path.exists():
        return send_from_directory(BASE_DIR / "static", "index.html")
    return "index.html not found", 404

@app.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    try:
        prefix = request.args.get('query', '').strip()
        if not prefix or len(prefix) < 2:
            return jsonify({'suggestions': []})

        words = prefix.split()
        last_word = words[-1] if words else prefix
        suggestions = autocomplete_trie.search_prefix(last_word, limit=5)

        if len(words) > 1:
            prefix_part = ' '.join(words[:-1]) + ' '
            suggestions = [prefix_part + sug for sug in suggestions]

        return jsonify({'suggestions': suggestions})
    except Exception as e:
        print(f"[v1] Autocomplete error: {e}")
        traceback.print_exc()
        return jsonify({'suggestions': []}), 500

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.json
        query = data.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Get document ids + scores
        doc_results = get_doc_ids(query)

        results = []
        for doc_name, score in doc_results[:50]:  # Top 50
            # Load metadata only when needed
            json_path = JSONS_DIR / f"{doc_name}.json"
            if not json_path.exists():
                json_path = JSONS_DIR / f"{doc_name}.xml.json"
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                metadata = doc_data.get('metadata', {})
                title = metadata.get('title', 'Untitled Document')
                authors = metadata.get('authors', [])
                author_str = ', '.join([
                    f"{a.get('first','')} {a.get('last','')}".strip()
                    for a in authors[:3]
                ])
                if len(authors) > 3:
                    author_str += ', et al.'
                abstract = ''
                if 'abstract' in doc_data and doc_data['abstract']:
                    if isinstance(doc_data['abstract'], list):
                        abstract = doc_data['abstract'][0].get('text', '')
                if not abstract and 'body_text' in doc_data and doc_data['body_text']:
                    if isinstance(doc_data['body_text'], list):
                        abstract = doc_data['body_text'][0].get('text','')[:300] + '...'

                url = doc_data.get('url', '')
                if not url:
                    paper_id = doc_data.get('paper_id', doc_name)
                    if paper_id.startswith('PMC'):
                        url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{paper_id}/"
                    else:
                        url = f"https://www.semanticscholar.org/paper/{paper_id}"

                results.append({
                    'id': doc_data.get('paper_id', doc_name),
                    'title': title or 'Untitled Document',
                    'authors': author_str or 'Unknown Authors',
                    'abstract': abstract,
                    'score': float(score),
                    'url': url,
                    'doc_name': doc_name
                })

        return jsonify({'results': results, 'total': len(results), 'query': query})

    except Exception as e:
        print(f"[v1] Search error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    try:
        data = request.json
        filename = data.get('filename', '')
        doc_data = data.get('data', {})
        if not filename or not doc_data:
            return jsonify({'error': 'Missing filename or document data'}), 400
        if 'paper_id' not in doc_data:
            return jsonify({'error': 'Document must have a paper_id'}), 400

        indexer = DocumentIndexer(BASE_DIR)
        result = indexer.index_document(doc_data, filename)

        return jsonify({
            'success': True,
            'paper_id': result['paper_id'],
            'terms_added': result['terms_added'],
            'barrels_updated': result['barrels_updated']
        })

    except Exception as e:
        print(f"[v1] Upload error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

