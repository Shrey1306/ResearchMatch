# ResearchMatch

ResearchMatch is a web application that helps students find research positions by matching their interests with faculty research areas. The application uses various matching algorithms and data sources to provide accurate and relevant matches.

## Features

- Multiple data sources: Scraping, DeepSeek, ChatGPT, Mistral, and Llama
- Different matching algorithms: Keyword-based, TF-IDF, and Word2Vec
- Research area search and filtering
- Detailed professor profiles with research areas and statistics
- Citation-based sorting options

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python
- Data Processing: NLTK, Gensim, scikit-learn
- Web Scraping: BeautifulSoup, Selenium
- LLM Integration: OpenAI API, DeepSeek, Mistral, Llama
- Deployment: Vercel Serverless and Fluid Compute

## Project Structure

```
ResearchMatch/
├── public/
│   ├── index.html      # Main application interface
│   ├── script.js       # Frontend logic
│   ├── styles.css      # Styling
│   └── results.json    # Professor/Researcher data
├── scripts/
│   ├── scraper.py      # Web scraping utilities
│   ├── llm.py          # LLM integration
│   └── open_source_llms.py  # Open source LLM integration
├── matching/
│   ├── matchers.py     # Matching algorithms
│   ├── preprocessors.py # Text preprocessing
│   ├── sorters.py      # Result sorting
│   └── vectorizers.py  # Text vectorization
└── llm_evals/
    └── evaluate_llms.py # LLM evaluation utilities
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables for API keys
4. Run the application: Will add this functionality if OSS interest is shown
   ```bash
   python app.py
   ```

## Usage

1. Visit the application at [research-match-six.vercel.app](https://research-match-six.vercel.app/)
2. Select your preferred data source and matching algorithm
3. Search for research areas or select from available topics
4. View matched professors and their research details

## Contributors

- <a href="https://github.com/Shrey1306" target="_blank">Shrey Gupta</a>
- <a href="https://github.com/abjoshipura" target="_blank">Akshara Joshipura</a>  
- <a href="https://github.com/shasha55055" target="_blank">Shasha</a>  
- <a href="https://github.com/uzairakbar" target="_blank">Uzair Akbar</a>

Built for CS4675: Internet Systems and Services
