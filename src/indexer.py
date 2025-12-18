from tokenizer import tokenize
from semantic_search import get_semantic_engine
import os
import json
import numpy as np
from collections import defaultdict
from pathlib import Path

lexicon = {}
next_term_id = 0
forward_index = {}
inverted_index = defaultdict(lambda: defaultdict(int))
doc_term_embeddings = {}  # {doc_id: {term: embedding_vector}}
doc_lengths = {}  # Store document lengths for BM25


def get_term_id(token):
    global next_term_id
    if token not in lexicon:
        lexicon[token] = next_term_id
        next_term_id += 1
    return lexicon[token]


def index_document(doc_id, data, use_semantic=True):
    """
    Index a document with optional semantic embedding storage.

    Args:
        doc_id: Document identifier
        data: JSON document data
        use_semantic: Whether to store term embeddings for semantic search
    """
    # extract sections separately
    title = data.get("metadata", {}).get("title", "")
    abstract_parts = data.get("abstract", [])
    body_parts = data.get("body_text", [])
    # combine abstract and body texts
    abstract_text = " ".join(item.get("text", "") for item in abstract_parts if isinstance(item, dict))
    body_text = " ".join(item.get("text", "") for item in body_parts if isinstance(item, dict))
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

    doc_length = len(title_tokens) + len(abstract_tokens) + len(body_tokens)
    doc_lengths[doc_id] = doc_length

    if use_semantic:
        semantic_engine = get_semantic_engine()
        if semantic_engine and semantic_engine.loaded:
            doc_embeddings = {}
            for token in term_counts.keys():
                if token in semantic_engine.embeddings:
                    doc_embeddings[token] = semantic_engine.embeddings[token].astype(np.float32)
            if doc_embeddings:
                doc_term_embeddings[doc_id] = doc_embeddings

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
        for term, term_id in sorted(lexicon.items(), key=lambda x: x[1]):
            f.write(f"{term}\t{term_id}\n")


def write_forward_index(path="forward_index.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for doc_id, term_ids in sorted(forward_index.items()):
            f.write(f"{doc_id}\t{' '.join(map(str, term_ids))}\n")


def write_inverted_index(path="inverted_index.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for term_id in sorted(inverted_index.keys()):
            postings = inverted_index[term_id]
            posting_list = " ".join(f"{doc_id}:{count}" for doc_id, count in sorted(postings.items()))
            f.write(f"{term_id}\t{posting_list}\n")


def write_doc_lengths(path="doc_lengths.txt"):
    """Save document lengths for BM25 scoring."""
    with open(path, "w", encoding="utf-8") as f:
        for doc_id, length in sorted(doc_lengths.items()):
            f.write(f"{doc_id}\t{length}\n")
    print(f"Saved document lengths for {len(doc_lengths)} documents to {path}")


def write_doc_embeddings(path="doc_embeddings.npz"):
    """Save document term embeddings in compressed numpy format."""
    if not doc_term_embeddings:
        return

    # Convert to a format suitable for numpy
    data_to_save = {}
    for doc_id, term_dict in doc_term_embeddings.items():
        # Store terms and their embeddings separately
        terms = list(term_dict.keys())
        embeddings = np.array([term_dict[term] for term in terms])
        data_to_save[f"{doc_id}_terms"] = np.array(terms, dtype=object)
        data_to_save[f"{doc_id}_embeddings"] = embeddings

    np.savez_compressed(path, **data_to_save)
    print(f"Saved embeddings for {len(doc_term_embeddings)} documents to {path}")


def write_all():
    write_lexicon()
    write_forward_index()
    write_inverted_index()
    write_doc_lengths()  # Write document lengths for BM25
    write_doc_embeddings()


def index_all_documents(json_folder="jsons", use_semantic=True):
    """
    Index all documents in the JSON folder.

    Args:
        json_folder: Path to folder containing JSON documents
        use_semantic: Whether to compute and store semantic embeddings
    """
    folder_path = Path(__file__).resolve().parent.parent / json_folder
    if not folder_path.exists():
        print(f"Warning: {folder_path} does not exist")
        return

    json_files = list(folder_path.glob("*.json"))
    print(f"Indexing {len(json_files)} documents from {folder_path}...")

    for i, file_path in enumerate(json_files, 1):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doc_id = data.get("paper_id", file_path.stem)
            index_document(doc_id, data, use_semantic=use_semantic)

            if i % 10 == 0:
                print(f"Indexed {i}/{len(json_files)} documents...")
        except Exception as e:
            print(f"Error indexing {file_path.name}: {e}")

    print(f"Writing indices...")
    write_all()
    print(f"Indexing complete! {len(lexicon)} unique terms, {len(forward_index)} documents")


if __name__ == "__main__":
    index_all_documents()
