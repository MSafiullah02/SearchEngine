from tokenizer import tokenize
from semantic_search import get_semantic_engine
import os
import json
import numpy as np
from collections import defaultdict
from pathlib import Path
from multiprocessing import Pool, cpu_count

lexicon = {}
next_term_id = 0
forward_index = {}
inverted_index = defaultdict(lambda: defaultdict(int))
doc_term_embeddings = {}
doc_lengths = {}  # Store document lengths for BM25


def get_term_id(token):
    global next_term_id
    if token not in lexicon:
        lexicon[token] = next_term_id
        next_term_id += 1
    return lexicon[token]


def tokenize_sections(title, abstract_parts, body_parts):
    """Tokenize all sections and return tokens with weights."""
    # Combine texts
    abstract_text = " ".join(item.get("text", "") for item in abstract_parts if isinstance(item, dict))
    body_text = " ".join(item.get("text", "") for item in body_parts if isinstance(item, dict))

    # Tokenize in batch
    title_tokens = tokenize(title)
    abstract_tokens = tokenize(abstract_text)
    body_tokens = tokenize(body_text)

    return title_tokens, abstract_tokens, body_tokens


def process_document_worker(file_path):
    """
    Worker function for parallel document processing.
    Only does tokenization - no embeddings to save RAM.
    Returns the processed data to be merged by main process.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc_id = data.get("paper_id", file_path.stem)

        title = data.get("metadata", {}).get("title", "")
        abstract_parts = data.get("abstract", [])
        body_parts = data.get("body_text", [])

        title_tokens, abstract_tokens, body_tokens = tokenize_sections(title, abstract_parts, body_parts)

        term_counts = defaultdict(int)

        # Section weights (standard: title 10x, abstract 5x, body 1x)
        for t in title_tokens:
            if not t.isdigit():
                term_counts[t] += 10
        for t in abstract_tokens:
            if not t.isdigit():
                term_counts[t] += 5
        for t in body_tokens:
            if not t.isdigit():
                term_counts[t] += 1

        doc_length = len(title_tokens) + len(abstract_tokens) + len(body_tokens)

        return {
            'doc_id': doc_id,
            'term_counts': dict(term_counts),
            'doc_length': doc_length,
            'success': True
        }

    except Exception as e:
        return {
            'file_path': str(file_path),
            'error': str(e),
            'success': False
        }


def write_lexicon(path="lexicon.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for term, term_id in sorted(lexicon.items(), key=lambda x: x[1]):  # Sort by term_id
            f.write(f"{term}\t{term_id}\n")


def write_forward_index(path="forward_index.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for doc_id, term_ids in sorted(forward_index.items()):  # Sort for consistency
            f.write(f"{doc_id}\t{' '.join(map(str, term_ids))}\n")


def write_inverted_index(path="inverted_index.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for term_id in sorted(inverted_index.keys()):  # Sort for consistency
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
        print("No embeddings to save (semantic search disabled or no embeddings found)")
        return

    data_to_save = {}
    for doc_id, term_dict in doc_term_embeddings.items():
        terms = list(term_dict.keys())
        embeddings = np.array([term_dict[term] for term in terms], dtype=np.float32)  # Use float32 to save memory
        data_to_save[f"{doc_id}_terms"] = np.array(terms, dtype=object)
        data_to_save[f"{doc_id}_embeddings"] = embeddings

    np.savez_compressed(path, **data_to_save)
    print(f"Saved embeddings for {len(doc_term_embeddings)} documents to {path}")


def write_all():
    print("Writing indices...")
    write_lexicon()
    write_forward_index()
    write_inverted_index()
    write_doc_lengths()  # Write document lengths
    write_doc_embeddings()
    print("All indices written successfully")


def index_all_documents(json_folder="jsons", use_semantic=True, num_workers=None):
    """
    Index all documents in the JSON folder with parallel processing.

    Args:
        json_folder: Path to folder containing JSON documents
        use_semantic: Whether to compute and store semantic embeddings
        num_workers: Number of parallel workers (None = use all CPU cores)
    """
    global lexicon, next_term_id, forward_index, inverted_index, doc_term_embeddings, doc_lengths

    folder_path = Path(__file__).resolve().parent.parent / json_folder
    if not folder_path.exists():
        print(f"Error: {folder_path} does not exist")
        return

    semantic_engine = None
    if use_semantic:
        print("Loading semantic engine in main process...")
        semantic_engine = get_semantic_engine()
        if semantic_engine and semantic_engine.loaded:
            print(f"Semantic engine loaded with {len(semantic_engine.embeddings)} embeddings")
        else:
            print("Warning: Semantic engine not available, indexing without embeddings")
            use_semantic = False

    json_files = list(folder_path.glob("*.json"))
    total_files = len(json_files)

    if num_workers is None:
        num_workers = cpu_count()

    print(f"Indexing {total_files} documents using {num_workers} CPU cores...")

    processed_count = 0
    error_count = 0

    with Pool(processes=num_workers) as pool:
        for i, result in enumerate(pool.imap_unordered(process_document_worker, json_files), 1):
            if result['success']:
                doc_id = result['doc_id']
                term_counts = result['term_counts']

                # Merge results into global indices
                term_ids = []
                for token, count in term_counts.items():
                    term_id = get_term_id(token)
                    term_ids.append(term_id)
                    inverted_index[term_id][doc_id] = count

                forward_index[doc_id] = term_ids
                doc_lengths[doc_id] = result['doc_length']

                if use_semantic and semantic_engine:
                    doc_embeddings = {}
                    for token in term_counts.keys():
                        if token in semantic_engine.embeddings:
                            doc_embeddings[token] = semantic_engine.embeddings[token].astype(np.float32)
                    if doc_embeddings:
                        doc_term_embeddings[doc_id] = doc_embeddings

                processed_count += 1
            else:
                error_count += 1
                print(f"Error indexing {result['file_path']}: {result['error']}")

            # Progress updates
            if i % 10 == 0 or i == total_files:
                progress = (i / total_files) * 100
                print(f"Progress: {i}/{total_files} ({progress:.1f}%) - {len(lexicon)} unique terms indexed")

    print(f"\nIndexing complete!")
    print(f"  - Documents processed: {processed_count}")
    print(f"  - Errors: {error_count}")
    print(f"  - Unique terms: {len(lexicon)}")
    print(f"  - Avg doc length: {sum(doc_lengths.values()) / len(doc_lengths):.1f} tokens")
    if use_semantic:
        print(f"  - Documents with embeddings: {len(doc_term_embeddings)}")

    write_all()


if __name__ == "__main__":
    index_all_documents()
