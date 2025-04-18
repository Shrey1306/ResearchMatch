import os
import json
import numpy as np
import pandas as pd


ROLLING_WINDOW: int = 1000
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


def rolling_mean(x: pd.DataFrame, window: int=ROLLING_WINDOW):
    return x.rolling(window, min_periods=1).mean()


def rolling_p05(x: pd.DataFrame, window: int=ROLLING_WINDOW):
    return x.rolling(
        window, min_periods=1
    ).apply(lambda w: np.percentile(w, 5), raw=True)


def rolling_p95(x: pd.DataFrame, window: int=ROLLING_WINDOW):
    return x.rolling(
        window, min_periods=1
    ).apply(lambda w: np.percentile(w, 95), raw=True)