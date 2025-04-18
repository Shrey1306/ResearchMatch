import os
import json


# path to store metrics
METRICS_FILE = 'dashboard/matching_metrics.json'


def load_metrics() -> dict[str, list]:
    '''
    load metrics from file if present.
    '''
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, 'r') as f:
            return json.load(f)
    return {
        'latency': [],
        'precision': [],
        'recall': [],
        'f1': [],
        'bleu': [],
        'rouge': []
    }


def save_metrics(metrics: dict[str, list]):
    '''save metrics to file.'''
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f)
