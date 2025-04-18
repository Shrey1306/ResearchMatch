from flask import Flask, request, jsonify
from matching.matchers import TFIDFMatcher, SortMetric

app = Flask(__name__)
matcher = TFIDFMatcher()

@app.route('/api/match', methods=['POST'])
def match_researchers():
    data = request.json
    query = data.get('query', '')
    use_tfidf = data.get('use_tfidf', False)
    sort_by = data.get('sort_by')
    
    if use_tfidf:
        # Use TF-IDF matching
        matches = matcher.get_matches(
            query=query,
            N=10,  # Number of matches to return
            sort_by=SortMetric[sort_by] if sort_by else None
        )
    else:
        # Use default key-value matching (implemented in frontend)
        matches = []
    
    return jsonify(matches)

if __name__ == '__main__':
    app.run(debug=True) 