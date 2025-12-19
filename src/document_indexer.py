from src.tokenizer import tokenize
from pathlib import Path
from collections import defaultdict
import json

class DocumentIndexer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.lexicon_dir = self.base_dir / "lexicon"
        self.inverted_index_dir = self.base_dir / "inverted_index"
        self.jsons_dir = self.base_dir / "jsons"
        
    def load_existing_lexicon(self):
        """Load all existing terms and their IDs from lexicon barrels"""
        lexicon = {}
        max_term_id = -1
        
        for i in range(1, 28):
            lexicon_file = self.lexicon_dir / f"lexicon{i}.txt"
            if lexicon_file.exists():
                with open(lexicon_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split('\t')
                            if len(parts) == 2:
                                term, term_id = parts
                                term_id = int(term_id)
                                lexicon[term] = term_id
                                max_term_id = max(max_term_id, term_id)
        
        return lexicon, max_term_id + 1
    
    def get_barrel_number_for_term(self, term):
        """Determine which lexicon barrel a term belongs to (1-27)"""
        ch = term[0].lower()
        if 'a' <= ch <= 'z':
            return ord(ch) - ord('a') + 1  # 1-26 for a-z
        else:
            return 27  # barrel 27 for non-alphabetic
    
    def get_barrel_number_for_term_id(self, term_id):
        """Determine which inverted index barrel a term_id belongs to (0-99)"""
        return term_id % 100
    
    def index_document(self, doc_data, filename):
        """Index a new document and update the appropriate barrels"""
        # Extract document ID
        doc_id = doc_data.get("paper_id", filename.split(".")[0])
        
        # Save JSON to jsons folder
        json_path = self.jsons_dir / filename
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)
        
        # Extract and tokenize text
        title = doc_data.get("metadata", {}).get("title", "")
        abstract_parts = doc_data.get("abstract", [])
        body_parts = doc_data.get("body_text", [])
        
        abstract_text = " ".join(item.get("text","") for item in abstract_parts if isinstance(item, dict))
        body_text = " ".join(item.get("text","") for item in body_parts if isinstance(item, dict))
        
        title_tokens = tokenize(title)
        abstract_tokens = tokenize(abstract_text)
        body_tokens = tokenize(body_text)
        
        # Section weights
        title_weight = 10
        abstract_weight = 5
        body_weight = 1
        
        # Accumulate weighted counts
        term_counts = defaultdict(int)
        for t in title_tokens:
            term_counts[t] += title_weight
        for t in abstract_tokens:
            term_counts[t] += abstract_weight
        for t in body_tokens:
            term_counts[t] += body_weight
        
        # Load existing lexicon
        lexicon, next_term_id = self.load_existing_lexicon()
        
        # Group new terms by barrel
        new_terms_by_barrel = defaultdict(list)
        # Group inverted index updates by barrel
        inverted_updates_by_barrel = defaultdict(list)
        
        terms_added = 0
        
        for token, count in term_counts.items():
            if token.isdigit():
                continue
            
            # Get or create term_id
            if token in lexicon:
                term_id = lexicon[token]
            else:
                term_id = next_term_id
                lexicon[token] = term_id
                next_term_id += 1
                terms_added += 1
                
                # Add to appropriate lexicon barrel
                barrel_num = self.get_barrel_number_for_term(token)
                new_terms_by_barrel[barrel_num].append(f"{token}\t{term_id}\n")
            
            # Add to appropriate inverted index barrel
            inv_barrel_num = self.get_barrel_number_for_term_id(term_id)
            inverted_updates_by_barrel[inv_barrel_num].append((term_id, doc_id, count))
        
        # Update lexicon barrels (append new terms)
        for barrel_num, terms in new_terms_by_barrel.items():
            lexicon_file = self.lexicon_dir / f"lexicon{barrel_num}.txt"
            with open(lexicon_file, 'a', encoding='utf-8') as f:
                f.writelines(terms)
        
        # Update inverted index barrels
        for barrel_num, updates in inverted_updates_by_barrel.items():
            inv_index_file = self.inverted_index_dir / f"inverted_index{barrel_num}.txt"
            
            # Load existing postings for this barrel
            postings = defaultdict(dict)
            if inv_index_file.exists():
                with open(inv_index_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split('\t')
                            if len(parts) == 2:
                                term_id_str, posting_list = parts
                                term_id = int(term_id_str)
                                for posting in posting_list.split():
                                    if ':' in posting:
                                        doc, cnt = posting.split(':')
                                        postings[term_id][doc] = int(cnt)
            
            # Add new postings
            for term_id, doc_id, count in updates:
                if doc_id in postings[term_id]:
                    postings[term_id][doc_id] += count
                else:
                    postings[term_id][doc_id] = count
            
            # Write back to barrel
            with open(inv_index_file, 'w', encoding='utf-8') as f:
                for term_id in sorted(postings.keys()):
                    posting_list = " ".join(f"{doc_id}:{count}" for doc_id, count in postings[term_id].items())
                    f.write(f"{term_id}\t{posting_list}\n")
        
        return {
            'paper_id': doc_id,
            'terms_added': terms_added,
            'barrels_updated': {
                'lexicon': list(new_terms_by_barrel.keys()),
                'inverted_index': list(inverted_updates_by_barrel.keys())
            }
        }
