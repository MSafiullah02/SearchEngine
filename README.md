Steps to set up the search engine
1. Clone or Download and extract this Repository
2. Download and extract https://nlp.stanford.edu/data/wordvecs/glove.2024.wikigiga.100d.zip
3. Move wiki_giga_2024_100_MFT20_vectors_seed_2024_alpha_0.75_eta_0.05.050_combined.txt to embedding/
4. Put your jsons (or go with the jsons in this repository) in the jsons folder
5. Run src/indexer.py
6. Run src/lexicon_barrel_maker.py
7. Run src/inverted_index_barrel_maker.py
8. Run app.py
9. Open http://localhost:5000/ on your browser
The first search loads the Semantic Search Embeddings so it takes longer than normal. All the next searches do not take a long time
