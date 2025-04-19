import os
import time
import nltk
import json
import redis
import threading
from typing import Any
from rouge import Rouge
from functools import wraps
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.bleu_score import SmoothingFunction

from dashboard.utils import load_metrics, save_metrics


# download NLTK utils
nltk.download('punkt')
# lock for file access
metrics_lock = threading.Lock()
redis_port = int(os.environ.get('REDIS_PORT'))
NUM_MATCHES: int = 10


try:    
    # connect redis
    redis_client = redis.Redis(
        host='localhost',
        port=redis_port,
        db=0,
        decode_responses=False
    )
    redis_client.ping()                 # test
    print('Successfully connected to Redis.')

    CACHE_ENABLED = True
    CACHE_EXPIRATION_SECONDS = 3600     # 1 hr cache

except redis.exceptions.ConnectionError as e:
    redis_client = None
    print(
        f'Warning: Could not connect to Redis at localhost:{redis_port}. Caching disabled. Error: {e}'
    )    
    CACHE_ENABLED = False


def calculate_metrics(
        query: str,
        matches: list[dict[str, Any]]
    ) -> dict[str, float]:
    '''
    Calculate performance metrics for different matches.
    '''
    if not matches:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'bleu': 0.0,
            'rouge': 0.0
        }
    
    # get research areas from matches
    research_areas = []
    for match in matches:
        areas = match.get('research_areas', [])
        if isinstance(areas, list):
            research_areas.extend(areas)
    
    # convert to sets for comparison
    query_words = set(query.lower().split())
    research_words = set(
        ' '.join(research_areas).lower().split()
    )
    
    # calculate metrics -- precision, recall, f1
    true_positives = len(
        query_words.intersection(research_words)
    )
    precision = (
        (true_positives / len(query_words))
        if query_words
        else 0.0
    )
    recall = (
        (true_positives / len(research_words))
        if research_words
        else 0.0
    )
    f1 = (
        (2 * (precision * recall) / (precision + recall))
        if (precision + recall) > 0
        else 0.0
    )
    
    # BLEU score
    reference = [query.lower().split()]
    candidate = ' '.join(research_areas).lower().split()
    smoothie = SmoothingFunction().method1
    bleu = sentence_bleu(
        reference, candidate, smoothing_function=smoothie
    )
    
    # ROUGE score
    rouge = Rouge()
    rouge_scores = rouge.get_scores(' '.join(research_areas), query)
    rouge_l = rouge_scores[0]['rouge-l']['f']
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'bleu': bleu,
        'rouge': rouge_l
    }


def monitor_matching(strategy_name: str):
    '''
    Decorator for match metrics + caching
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            query = kwargs.get('query', '')
            if not query and len(args) > 1:
                if isinstance(args[1], (str, list)):
                    query = args[1]
            # convert list query to str for key
            query_key_part = (
                '|'.join(query) if isinstance(query, list) else query
            )

            cache_hit = False
            matches = None
            latency = 0.0
            metrics = {}
            effective_strategy_name = strategy_name

            if CACHE_ENABLED:
                # make cache key
                N = kwargs.get('N', NUM_MATCHES)
                sort_by_metric = kwargs.get('sort_by')
                sort_by = sort_by_metric.name if sort_by_metric else 'None'
                sort_reverse = kwargs.get('sort_reverse', True)
                cache_key = (
                    f'matcher_cache:{strategy_name}:{query_key_part}:{N}:{sort_by}:{sort_reverse}'
                )
                
                try:
                    # check hit
                    cached_result_json = redis_client.get(cache_key)
                    if cached_result_json:
                        # read cache
                        matches = json.loads(cached_result_json)
                        
                        latency = time.time() - start_time
                        cache_hit = True
                        
                        effective_strategy_name = f'{strategy_name} (Cache Hit)'
                        
                        # cache-hit metrics
                        metrics = calculate_metrics(query_key_part, matches) 
                        
                        print(
                            f'Cache hit for {strategy_name} with query "{query_key_part[:30]}..."'
                        )
                except redis.exceptions.RedisError as e:
                    print(
                        f'Redis Error during GET: {e}. Proceeding without cache.'
                    )
                except json.JSONDecodeError as e:
                    print(
                        f'Error decoding cached JSON for key {cache_key}: {e}. Ignoring cache.'
                    )
                    matches = None
                    cache_hit = False

            # cache miss
            if not cache_hit:
                # call matching function
                matches = func(*args, **kwargs)
                
                # total latency == cache check (miss) + matching
                latency = time.time() - start_time 
                
                # get metrics
                metrics = calculate_metrics(
                    query_key_part, matches
                )

                # cache result
                if CACHE_ENABLED and matches is not None:
                    try:
                        # make cache key
                        N = kwargs.get('N', NUM_MATCHES)
                        sort_by_metric = kwargs.get('sort_by')
                        sort_by = sort_by_metric.name if sort_by_metric else 'None'
                        sort_reverse = kwargs.get('sort_reverse', True)
                        cache_key = (
                            f'matcher_cache:{strategy_name}:{query_key_part}:{N}:{sort_by}:{sort_reverse}'
                        )
                        
                        matches_json = json.dumps(matches)
                        redis_client.setex(
                            cache_key, CACHE_EXPIRATION_SECONDS, matches_json
                        )
                    except redis.exceptions.RedisError as e:
                        print(
                            f'Redis Error during SETEX: {e}. Result not cached.'
                        )
                    except TypeError as e:
                        print(
                            f'Error serializing matches to JSON for caching: {e}. Result not cached.'
                        )

            # log metrics
            if matches is not None:
                with metrics_lock:
                    metrics_history = load_metrics()
                    timestamp = int(start_time)
                    
                    metrics_history['latency'].append([
                        effective_strategy_name, timestamp, latency
                    ])
                    metrics_history['precision'].append([
                        effective_strategy_name, timestamp, metrics.get('precision', 0.0)
                    ])
                    metrics_history['recall'].append([
                        effective_strategy_name, timestamp, metrics.get('recall', 0.0)
                    ])
                    metrics_history['f1'].append([
                        effective_strategy_name, timestamp, metrics.get('f1', 0.0)
                    ])
                    metrics_history['bleu'].append([
                        effective_strategy_name, timestamp, metrics.get('bleu', 0.0)
                    ])
                    metrics_history['rouge'].append([
                        effective_strategy_name, timestamp, metrics.get('rouge', 0.0)
                    ])
                    
                    save_metrics(metrics_history)
            
            return matches
        return wrapper
    return decorator 