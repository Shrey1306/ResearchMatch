# ResearchMatch

Find a Research Position in less than 60 seconds.

This project helps students find potential research advisors by scraping university faculty directories, extracting relevant information, and providing a searchable web interface.

## Features

*   Scrapes faculty directory pages to gather professor information (name, title, email, profile links, etc.).
*   Extracts research areas and publication statistics from faculty profiles and Google Scholar.
*   Uses LLMs (DeepSeek/ChatGPT) to further analyze professor details and research interests (via `llm.py`).
*   Provides a simple web frontend (`public/`) to browse and select research topics and view potential advisor profiles.

## Project Structure

```
/ResearchMatch
├── public/                 # Frontend files (served to the browser)
│   ├── index.html
│   ├── styles.css
│   ├── script.js
│   └── results.json        # Generated data for the frontend
│
├── scripts/                # Python scripts for data processing
│   ├── scraper.py          # Scrapes faculty directory and profiles
│   ├── llm.py              # Uses LLMs to analyze professor data
│   └── temp.py             # Temporary/utility script
│
├── matching/               # Python scripts for search / matching
│   ├── matchers.py         # Similarity metrics and matching
│   ├── preprocessors.py    # Text preprocessing and cleaning
│   ├── sorters.py          # Text preprocessing and cleaning
│   ├── evaluator.py        # Evaluation scripts for different matching strategies
│   └── vectorizers.py      # Vector embeddings for text
│
├── dashboard/              # Package for metrics monitoring dashboard
│   ├── __init__.py         # 
│   ├── app.py              # Dashboard definition
│   ├── utils.py            # Helper functions for metric storage
│   └── monitor.py          # Metrics monitoring and storage
│
├── .env                    # Environment variables (API keys, config) - DO NOT COMMIT
├── .gitignore              # Files/folders ignored by Git
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd ResearchMatch
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Copy the `.env.example` file (if you create one) or create a new `.env` file.
    *   Add your API keys and any other necessary configuration:
        ```dotenv
        DEEPSEEK_API_KEY=your_deepseek_api_key_here
        CHATGPT_API_KEY=your_chatgpt_api_key_here
        UNIVERSITY="Georgia Institute of Technology"
        DIRECTORY_BASE_URL="https://www.cc.gatech.edu/people/faculty?page="
        PROFILE_BASE_URL="https://www.cc.gatech.edu"
        NUM_DIRECTORY_PAGES=24 
        ```
    *   **Important:** Ensure `.env` is listed in your `.gitignore` file and **never commit it** to your repository.

## Usage

1.  **Run the Scraper:**
    *   This script populates `public/results.json` with data scraped from the university directory and profiles.
    ```bash
    cd scripts
    python scraper.py
    cd ..
    ```

2.  **Run LLM Analysis (Optional):**
    *   The `llm.py` script can be used to get more detailed analysis for a specific professor using LLMs. Modify the script to specify the professor's name.
    ```bash
    cd scripts
    python llm.py 
    cd ..
    ```

3.  **Retrieve Matches (Optional):**
    *   We can use `matchers.Matcher` classes to retrieve top-N matches for a given query. Example:
    ```python
    from matching.matchers import TFIDFMatcher
    from matching.sorters import SortMetric

    # TF-IDF based matching
    matcher = TFIDFMatcher()
    matches = matcher.get_matches(
        'machine learning',
        N=5,
        sort_by=SortMetric.CITATIONS
    )
    ```

4.  **Monitoring Metrics (Optional):**
    * With each call to the `matchers.Matcher.get_matches` function, the corresponding query metrics would be calculated and saved under `streamlit/matching_metrics.json`. These include precision, recall, F1-scores, BLEU scores and ROUGE socres. To launch the dashboard, simply run
    ```bash
    python -m streamlit run dashboard/app.py
    ```

## Contributing

[Details on how to contribute, if applicable]

## License

[Specify your project's license, e.g., MIT License]
