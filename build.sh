#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Generate TF-IDF matcher JavaScript
python scripts/generate_tfidf_js.py