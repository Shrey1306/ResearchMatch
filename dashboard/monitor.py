import time
import nltk
from typing import Any
from rouge import Rouge
from functools import wraps
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.bleu_score import SmoothingFunction

from dashboard.utils import load_metrics, save_metrics


# download NLTK utils
nltk.download('punkt')


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
    Decorator to monitoring matching performance.
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # get query from args or kwargs
            query = kwargs.get('query', '')
            if not query and len(args) > 1:
                query = args[1]
            
            # execute matching function
            matches = func(*args, **kwargs)
            
            # measure latency
            latency = time.time() - start_time
            
            # measure other metrics
            metrics = calculate_metrics(query, matches)
            
            # load metrics history
            metrics_history = load_metrics()
            
            # update metric history
            metrics_history['latency'].append([strategy_name, latency])
            metrics_history['precision'].append([strategy_name, metrics['precision']])
            metrics_history['recall'].append([strategy_name, metrics['recall']])
            metrics_history['f1'].append([strategy_name, metrics['f1']])
            metrics_history['bleu'].append([strategy_name, metrics['bleu']])
            metrics_history['rouge'].append([strategy_name, metrics['rouge']])
            
            # save metrics history
            save_metrics(metrics_history)
            
            return matches
        return wrapper
    return decorator 