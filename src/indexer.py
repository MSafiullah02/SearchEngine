from tokenizer import tokenize
import os
import json
from collections import defaultdict
lexicon = {}
next_term_id = 0
forward_index = {}
inverted_index = defaultdict(lambda: defaultdict(int))

def get_term_id(token):
    global next_term_id
    if token not in lexicon:
        lexicon[token] = next_term_id
        next_term_id += 1
    return lexicon[token]

def index_document(doc_id, data):
    # extract sections separately
    title = data.get("metadata", {}).get("title", "")
    abstract_parts = data.get("abstract", [])
    body_parts = data.get("body_text", [])
    # combine abstract and body texts
    abstract_text = " ".join(item.get("text","") for item in abstract_parts if isinstance(item, dict))
    body_text = " ".join(item.get("text","") for item in body_parts if isinstance(item, dict))
    # tokenize each section
    title_tokens = tokenize(title)
    abstract_tokens = tokenize(abstract_text)
    body_tokens = tokenize(body_text)
    # section weights
    title_weight = 10
    abstract_weight = 5
    body_weight = 1
    # accumulate weighted counts
    term_counts = defaultdict(int)
    for t in title_tokens:
        term_counts[t] += title_weight
    for t in abstract_tokens:
        term_counts[t] += abstract_weight
    for t in body_tokens:
        term_counts[t] += body_weight
    term_ids = []
    for token, count in term_counts.items():
        if token.isdigit():
            continue
        term_id = get_term_id(token)
        term_ids.append(term_id)
        inverted_index[term_id][doc_id] += count
    forward_index[doc_id] = term_ids

def write_lexicon(path="lexicon.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for term, term_id in lexicon.items():
            f.write(f"{term}\t{term_id}\n")

def write_forward_index(path="forward_index.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for doc_id, term_ids in forward_index.items():
            f.write(f"{doc_id}\t{' '.join(map(str, term_ids))}\n")

def write_inverted_index(path="inverted_index.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for term_id, postings in inverted_index.items():
            posting_list = " ".join(f"{doc_id}:{count}" for doc_id, count in postings.items())
            f.write(f"{term_id}\t{posting_list}\n")

def write_all():
    write_lexicon()
    write_forward_index()
    write_inverted_index()

def index_all_documents(json_folder="../jsons"):
    folder_path = os.path.join(os.path.dirname(__file__), json_folder)
    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc_id = data.get("paper_id", filename.split(".")[0])
        index_document(doc_id, data)
    write_all()
if __name__ == "__main__":
    index_all_documents()
