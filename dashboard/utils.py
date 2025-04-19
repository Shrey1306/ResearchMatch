"""
ResearchMatch Dashboard Utilities

This module provides utility functions for the ResearchMatch dashboard,
including metric persistence and statistical calculations for visualization.

The module handles:
- Loading and saving performance metrics
- Computing rolling statistics for trend analysis
- Calculating confidence intervals
"""

import os
import json
import numpy as np
import pandas as pd


ROLLING_WINDOW: int = 1000
METRICS_FILE = 'dashboard/matching_metrics.json'


def load_metrics() -> dict[str, list]:
    """
    Load performance metrics from the metrics file.
    
    Returns:
        Dictionary containing lists of metrics:
        - latency: Query response times
        - precision: Matching precision scores
        - recall: Matching recall scores
        - f1: F1 scores
        - bleu: BLEU scores
        - rouge: ROUGE scores
    """
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
    """
    Save performance metrics to the metrics file.
    
    Args:
        metrics: Dictionary containing lists of performance metrics
    """
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f)


def rolling_mean(x: pd.DataFrame, window: int=ROLLING_WINDOW):
    """
    Calculate rolling mean over a window of values.
    
    Args:
        x: Input data series
        window: Size of the rolling window
        
    Returns:
        Series containing rolling mean values
    """
    return x.rolling(window, min_periods=1).mean()


def rolling_p05(x: pd.DataFrame, window: int=ROLLING_WINDOW):
    """
    Calculate rolling 5th percentile over a window.
    
    Args:
        x: Input data series
        window: Size of the rolling window
        
    Returns:
        Series containing rolling 5th percentile values
    """
    return x.rolling(
        window, min_periods=1
    ).apply(lambda w: np.percentile(w, 5), raw=True)


def rolling_p95(x: pd.DataFrame, window: int=ROLLING_WINDOW):
    """
    Calculate rolling 95th percentile over a window.
    
    Args:
        x: Input data series
        window: Size of the rolling window
        
    Returns:
        Series containing rolling 95th percentile values
    """
    return x.rolling(
        window, min_periods=1
    ).apply(lambda w: np.percentile(w, 95), raw=True)