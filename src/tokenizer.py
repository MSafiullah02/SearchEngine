import re
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
STOPWORDS = set(stopwords.words('english'))
stemmer = PorterStemmer()
def tokenize(text):
    text = text.lower()
    # split by any sequence of non-alphanumeric characters
    tokens = re.split(r'[^a-z0-9]+', text)
    cleaned = []
    for token in tokens:
        if not token:
            continue
        if token in STOPWORDS:
            continue
        stemmed = stemmer.stem(token)
        cleaned.append(stemmed)
    return cleaned
