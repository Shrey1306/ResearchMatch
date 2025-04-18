import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from matching.matchers import TFIDFMatcher
import numpy as np

def generate_tfidf_js():
    try:
        print("Initializing TFIDFMatcher...")
        # Initialize the matcher
        matcher = TFIDFMatcher()
        
        print("Getting vectors and vocabulary...")
        # Get the precomputed vectors and vocabulary
        vectors = matcher.entry_vectors
        vocabulary = matcher.vectorizer.vectorizer.get_feature_names_out()
        
        print("Converting vectors to JSON...")
        # Convert numpy arrays to lists for JSON serialization
        vectors_js = {str(k): v.tolist() for k, v in vectors.items()}
        
        print("Creating JavaScript code...")
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
        
        print("Ensuring public directory exists...")
        # Ensure the public directory exists
        os.makedirs('public', exist_ok=True)
        
        print("Writing to tfidf_matcher.js...")
        # Write to file
        with open('public/tfidf_matcher.js', 'w') as f:
            f.write(js_code)
            
        print("Successfully generated tfidf_matcher.js")
        
    except Exception as e:
        print(f"Error generating tfidf_matcher.js: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    generate_tfidf_js() 