from flask import Flask, request, jsonify
from flask_cors import CORS
from matching.matchers import TFIDFMatcher, SortMetric
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
matcher = TFIDFMatcher()

@app.route('/api/match', methods=['POST'])
def match_researchers():
    try:
        data = request.json
        query = data.get('query', '')
        use_tfidf = data.get('use_tfidf', False)
        sort_by = data.get('sort_by')
        
        if not use_tfidf:
            return jsonify([])
            
        # Use TF-IDF matching
        matches = matcher.get_matches(
            query=query,
            N=10,  # Number of matches to return
            sort_by=SortMetric[sort_by] if sort_by else None
        )
        
        return jsonify(matches)
        
    except Exception as e:
        print(f"Error in match_researchers: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': 'An error occurred while processing your request',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 