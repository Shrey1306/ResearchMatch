import json
import os
from matching.matchers import TFIDFMatcher
import numpy as np

def generate_tfidf_js():
    # Initialize the matcher
    matcher = TFIDFMatcher()
    
    # Get the precomputed vectors and vocabulary
    vectors = matcher.entry_vectors
    vocabulary = matcher.vectorizer.vectorizer.get_feature_names_out()
    
    # Convert numpy arrays to lists for JSON serialization
    vectors_js = {str(k): v.tolist() for k, v in vectors.items()}
    
    # Create JavaScript code
    js_code = f"""
// TF-IDF matching functionality
const tfidfVectors = {json.dumps(vectors_js)};
const vocabulary = {json.dumps(vocabulary.tolist())};
const researchers = {json.dumps(matcher.data)};

function cosineSimilarity(vec1, vec2) {{
    const dotProduct = vec1.reduce((sum, val, i) => sum + val * vec2[i], 0);
    const norm1 = Math.sqrt(vec1.reduce((sum, val) => sum + val * val, 0));
    const norm2 = Math.sqrt(vec2.reduce((sum, val) => sum + val * val, 0));
    return dotProduct / (norm1 * norm2);
}}

function getTFIDFMatches(query, N = 10) {{
    // Convert query to vector using the same vocabulary
    const queryTerms = query.toLowerCase().split(/\\s+/);
    const queryVector = new Array(vocabulary.length).fill(0);
    
    queryTerms.forEach(term => {{
        const index = vocabulary.indexOf(term);
        if (index !== -1) {{
            queryVector[index] = 1;  // Simple binary representation
        }}
    }});
    
    // Calculate similarities
    const similarities = [];
    for (const [i, vector] of Object.entries(tfidfVectors)) {{
        if (vector.some(v => v !== 0)) {{  // Skip zero vectors
            const similarity = cosineSimilarity(queryVector, vector);
            similarities.push({{index: parseInt(i), similarity}});
        }}
    }}
    
    // Sort by similarity and get top N
    similarities.sort((a, b) => b.similarity - a.similarity);
    const topIndices = similarities.slice(0, N).map(item => item.index);
    return topIndices.map(i => researchers[i]);
}}
"""
    
    # Ensure the public directory exists
    os.makedirs('public', exist_ok=True)
    
    # Write to file
    with open('public/tfidf_matcher.js', 'w') as f:
        f.write(js_code)

if __name__ == '__main__':
    generate_tfidf_js() 