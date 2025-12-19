# Semantic Search Engine Project

## Overview
This project implements a semantic search engine that allows users to search documents based on meaning rather than exact keyword matching. The system preprocesses a large text corpus, builds indexing structures (lexicon, barrels, and indexes), and uses pre-trained word embeddings to enable semantic similarity during search.

The application runs as a web service and can be accessed through a browser.

---

## Dataset Requirements
This project is designed to work with **JSON-based document datasets**.  
Originally, the system was tested using the **CORD-19 dataset**, which can be downloaded from:

https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/historical_releases/cord-19_2020-05-27.tar.gz

### Dataset Setup
- After downloading and extracting the dataset:
  - Create a folder named **`jsons`** in the project root directory.
  - Place **all extracted JSON files** inside the `jsons` folder.

> **Note:**  
> Users are not restricted to this dataset. Any dataset containing textual documents in JSON format may be used. The provided scripts can be run on any compatible dataset to generate the required indexes.

---

## Embedding Requirements
The semantic search functionality relies on **pre-trained word embeddings**.

### Required Embeddings
- **GloVe embeddings (100-dimensional)**
- Download from:
  
  https://nlp.stanford.edu/data/wordvecs/glove.2024.wikigiga.100d.zip

### Embedding Setup
1. Download and extract the ZIP file.
2. Create a folder named **`embeddings`** in the project root directory.
3. Place the extracted `.txt` embedding file inside the `embeddings` folder.

These embeddings are used to compute semantic similarity between queries and documents.

---

## Indexing and Execution
After setting up the dataset and embeddings:

1. Run the provided scripts to generate:
   - Lexicon
   - Barrels
   - Index files
2. Start the application.
3. Open the following URL in your browser:
