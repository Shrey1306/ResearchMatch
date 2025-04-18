import os
import sys
import time
import json
import random
import argparse
import concurrent.futures
from typing import Any, Optional

import nltk
try:
    from nltk.corpus import words as nltk_words
except ImportError:
    nltk.download('words')
    from nltk.corpus import words as nltk_words

# adjust path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from matching.matchers import TFIDFMatcher, Word2VecMatcher, Matcher, NUM_MATCHES
from matching.sorters import SortMetric


# configs
DATA_PATH = 'public/results.json'
MAX_WORKERS = 10        # concurrent threads
WORDS_PER_QUERY = 3     # random words per query
POISSON_LAMBDA = 5.0    # Poisson distribution for requests per second
NUM_NOVEL_WORDS = 3     # novel words per query


def load_research_words(data_path: str) -> set[str]:
    '''
    Loads data ande extracts unique research areas.
    '''
    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(
            f'Error: Data file not found at {data_path}'
        )
        sys.exit(1)
    except json.JSONDecodeError:
        print(
            f'Error: Could not decode JSON from {data_path}'
        )
        sys.exit(1)

    words = set()
    for entry in data:
        research_areas = entry.get('research_areas', [])
        if research_areas and isinstance(research_areas, list):
            for area in research_areas:
                if area and isinstance(area, str):
                    # tokenization
                    words.update(area.lower().split())
    
    # remove stop words and common short words
    words = {word for word in words if len(word) > 2}
    
    if not words:
        print(
            'Warning: No research area words found. Queries will be empty.'
        )
        # return empty
        return set()
        
    return words


def get_novel_words(research_words_set: set[str]) -> list[str]:
    '''
    Gets a list of common English words not present in research areas.
    '''
    if not nltk or not nltk_words:
        print('NLTK not available, cannot generate novel words.')
        return []

    try:
        all_nltk_words = nltk_words.words()
    except LookupError:
        print(f'Error: NLTK words corpus not found.')
        print(
            'Please download it: python -m nltk.downloader words'
        )
        return []
        
    # lower case
    lower_research_words = {
        word.lower() for word in research_words_set
    }
    
    novel_word_candidates = [
        word.lower() for word in all_nltk_words 
        if len(word) > 2 and word.isalpha() and word.lower() not in lower_research_words
    ]
    
    if not novel_word_candidates:
        print(
            'Warning: Could not find any novel words from NLTK corpus.'
        )
        return []
        
    print(
        f'Found {len(novel_word_candidates)} potential novel words from NLTK corpus.'
    )
    return novel_word_candidates

def generate_random_query(
    research_words_list: list[str], 
    novel_words_list: list[str],
    num_research_words: int, 
    num_novel_words: int
) -> str:
    '''Generates a random query string including research and novel words.'''
    selected_words = []

    # Select research words
    if research_words_list:
        num_to_sample = min(num_research_words, len(research_words_list))
        selected_words.extend(random.sample(research_words_list, num_to_sample))

    # Select novel words
    if novel_words_list and num_novel_words > 0:
        num_to_sample = min(num_novel_words, len(novel_words_list))
        selected_words.extend(random.sample(novel_words_list, num_to_sample))
    
    if not selected_words:
        return '' # Avoid empty query if both lists were empty
        
    # Shuffle the combined list
    random.shuffle(selected_words)
    
    return ' '.join(selected_words)

def run_match_query(
    matcher_instance: Matcher,
    query: str,
    sort_metric: Optional[SortMetric],
    run_id: int
):
    '''Runs a single matching query and prints basic info.'''
    matcher_name = type(matcher_instance).__name__
    sort_name = sort_metric.name if sort_metric else 'DefaultSimilarity'
    start_time = time.monotonic()
    try:
        results = matcher_instance.get_matches(
            query=query,
            N=NUM_MATCHES,
            sort_by=sort_metric,
            sort_reverse=True # Assuming descending sort is usually desired
        )
        duration = time.monotonic() - start_time
        print(
            f'Run {run_id}: OK - {matcher_name} | Sort: {sort_name} | Query: "{query[:30]}..." | Duration: {duration:.4f}s | Results: {len(results)}'
        )
    except Exception as e:
        duration = time.monotonic() - start_time
        print(
            f'Run {run_id}: FAILED - {matcher_name} | Sort: {sort_name} | Query: "{query[:30]}..." | Duration: {duration:.4f}s | Error: {e}'
        )

def main(duration_seconds: int):
    print(f'Starting stress test for {duration_seconds} seconds...')
    print(f'Target request rate (Poisson lambda): {POISSON_LAMBDA} requests/sec')
    
    if POISSON_LAMBDA <= 0:
        print('Error: POISSON_LAMBDA must be positive.')
        sys.exit(1)

    research_words_set = load_research_words(DATA_PATH)
    if not research_words_set:
        print('Exiting due to lack of research words for query generation.')
        return
    research_words_list = list(research_words_set)
    
    # Prepare novel words list
    novel_words_list = get_novel_words(research_words_set)

    # Instantiate matchers once
    matchers = [TFIDFMatcher(DATA_PATH), Word2VecMatcher(DATA_PATH)]
    
    # Available sort metrics (excluding CUSTOM for simplicity)
    sort_options = [None] + [metric for metric in SortMetric if metric != SortMetric.CUSTOM]

    start_time = time.time()
    end_time = start_time + duration_seconds
    run_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        while time.time() < end_time:
            # Calculate delay until next submission using exponential distribution
            # The average time between requests is 1 / lambda
            try:
                delay = random.expovariate(POISSON_LAMBDA)
            except ValueError:
                print('Error: POISSON_LAMBDA must be positive.') # Should be caught earlier, but defensive check
                break 
                
            # Sleep for the calculated delay
            time.sleep(delay)

            # Check if time limit exceeded during sleep
            if time.time() >= end_time:
                break

            # Remove completed futures
            done_futures = [f for f in futures if f.done()]
            for future in done_futures:
                futures.remove(future)
                try:
                    future.result() # Check for exceptions in completed tasks
                except Exception as exc:
                    print(f'A task generated an exception: {exc}')

            # Submit a new task if a worker is available
            if len(futures) < MAX_WORKERS:
                run_count += 1
                matcher = random.choice(matchers)
                sorter = random.choice(sort_options)
                query = generate_random_query(
                    research_words_list, 
                    novel_words_list,
                    WORDS_PER_QUERY, 
                    NUM_NOVEL_WORDS
                )
                
                future = executor.submit(run_match_query, matcher, query, sorter, run_count)
                futures.append(future)
            # else: # Optional: Log if workers are full
                # print(f'Workers full ({len(futures)}/{MAX_WORKERS}), delaying submission {run_count+1}')


        print(f'\nTest duration ({duration_seconds}s) reached or error occurred. Waiting for pending tasks...')
        # Wait for remaining futures to complete
        concurrent.futures.wait(futures)

    print(f'\nStress test finished. Total runs initiated: {run_count}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Stress test matching algorithms.'
    )
    parser.add_argument(
        'duration', 
        type=int, 
        help='Duration of the test in seconds.'
    )
    args = parser.parse_args()
    
    main(args.duration) 