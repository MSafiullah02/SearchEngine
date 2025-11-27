import os
import json
def get_documents(base_path):
    for fname in os.listdir(base_path):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(base_path, fname)
        with open(fpath, "r", encoding="utf8") as f:
            data = json.load(f)
        doc_id = data.get("paper_id", fname)
        # Extract text
        text = ""
        # Abstract
        abstract_parts = data.get("abstract", [])
        if isinstance(abstract_parts, list):
            for item in abstract_parts:
                text += " " + item.get("text", "")
        else:
            text += " " + abstract_parts
        # Body text
        for item in data.get("body_text", []):
            text += " " + item.get("text", "")
        yield doc_id, text.strip()