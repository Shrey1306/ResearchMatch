import os
import sys
import time
import json
import nltk
import random
import argparse
import concurrent.futures
from typing import Any, Optional
from nltk.corpus import words as nltk_words

# adjust path to import from parent directory
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from matching.sorters import SortMetric
from matching.matchers import (
    NUM_MATCHES,
    Matcher,
    TFIDFMatcher,
    Word2VecMatcher,
    KeywordMatcher,
    DeepseekMatcher,
)


nltk.download('words')


# configs
DATA_PATH: str = 'public/results.json'
MAX_WORKERS: int = 10                   # concurrent threads
WORDS_PER_QUERY: int = 5                # random words per query
POISSON_LAMBDA: float = 5.0             # poisson distribution for requests per second
NUM_NOVEL_WORDS: int = 5                # novel words per query
REPEAT_QUERY_PROBABILITY: float = 0.1   # probability to repeat query
RECENT_QUERY_BUFFER_SIZE: int = 50      # number of recent queries to use for repeating
recent_queries: list[str] = []


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
        if isinstance(research_areas, dict):
            research_areas = research_areas.values()
            research_areas = [x for x in research_areas if x]
            research_areas = sum(research_areas, [])
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
    all_nltk_words = nltk_words.words()
        
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
        f'Using {len(novel_word_candidates)} novel words from NLTK corpus.'
    )
    return novel_word_candidates


def generate_random_query(
    research_words_list: list[str], 
    novel_words_list: list[str],
    base_num_research_words: int,
    base_num_novel_words: int
) -> str:
    '''
    Generates random query with research and novel/dummy words.
    '''
    # randomize word counts
    num_research_words = random.randint(
        max(0, base_num_research_words - 3), 
        base_num_research_words + 3
    )
    num_novel_words = random.randint(
        max(0, base_num_novel_words - 3),
        base_num_novel_words + 3
    )

    selected_words = []

    # sample research words
    if research_words_list and num_research_words > 0:
        num_to_sample = min(
            num_research_words, len(research_words_list)
        )
        selected_words.extend(
            random.sample(research_words_list, num_to_sample)
        )

    # sample novel/dummy words
    if novel_words_list and num_novel_words > 0:
        num_to_sample = min(
            num_novel_words, len(novel_words_list)
        )
        selected_words.extend(
            random.sample(novel_words_list, num_to_sample)
        )
    
    if not selected_words:
        return ''   # empty query
        
    # shuffle query words
    random.shuffle(selected_words)
    
    return ' '.join(selected_words)


def run_match_query(
    matcher_instance: Matcher,
    query: str,
    sort_metric: Optional[SortMetric],
    run_id: int
):
    '''
    Sends a matching query.
    '''
    matcher_name = type(matcher_instance).__name__

    sort_name = (
        sort_metric.name if sort_metric else 'DefaultSimilarity'
    )
    start_time = time.monotonic()
    try:
        results = matcher_instance.get_matches(
            query=query,
            N=NUM_MATCHES,
            sort_by=sort_metric,
            sort_reverse=True
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

    print(
        f'Starting metrics test for {duration_seconds} seconds...'
    )
    print(
        f'Request rate (Poisson lambda): {POISSON_LAMBDA} requests/sec'
    )

    research_words_set = load_research_words(DATA_PATH)
    if not research_words_set:
        print(
            'No research words for query generation.'
        )
        return
    research_words_list = list(research_words_set)
    
    # get novel/dummy words
    novel_words_list = get_novel_words(research_words_set)

    # init matchers
    matchers = ([
        TFIDFMatcher(DATA_PATH), Word2VecMatcher(DATA_PATH), KeywordMatcher(DATA_PATH)
    ])
    
    # init sorters
    sort_options = (
        [None]
        +
        [metric for metric in SortMetric if metric != SortMetric.CUSTOM]
    )

    start_time = time.time()
    end_time = start_time + duration_seconds
    run_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        threads = []
        while time.time() < end_time:
            # calculate delay until next query
            delay = random.expovariate(POISSON_LAMBDA)
                
            # sleep until next query
            time.sleep(delay)

            # time up?
            if time.time() >= end_time:
                break

            # remove completed threads
            done_threads = [t for t in threads if t.done()]
            for thread in done_threads:
                threads.remove(thread)
                try:
                    thread.result()     # check if successfully completed
                except Exception as e:
                    print(
                        f'A task generated an exception: {e}'
                    )

            # submit task if thread available
            if len(threads) < MAX_WORKERS:
                run_count += 1
                matcher = random.choice(matchers)
                sorter = random.choice(sort_options)
                
                # make or repeat query
                if recent_queries and random.random() < REPEAT_QUERY_PROBABILITY:
                    # repeat query
                    query = random.choice(recent_queries)
                else:
                    # new query
                    query = generate_random_query(
                        research_words_list, 
                        novel_words_list,
                        WORDS_PER_QUERY, 
                        NUM_NOVEL_WORDS
                    )
                    # add to recent queries
                    if query:
                        recent_queries.append(query)
                        if len(recent_queries) > RECENT_QUERY_BUFFER_SIZE:
                            recent_queries.pop(0)       # pop oldest
                
                thread = executor.submit(
                    run_match_query, matcher, query, sorter, run_count
                )
                threads.append(thread)


        print(
            f'\nTest duration ({duration_seconds}s) reached or error occurred. Waiting for pending threads...'
        )
        # wait for threads to complete
        concurrent.futures.wait(threads)

    print(
        f'\nStress test finished. Total runs initiated: {run_count}'
    )


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