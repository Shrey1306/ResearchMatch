from typing import Any, Callable
from enum import Enum
import numpy as np

class SortMetric(Enum):
    CITATIONS = "citations"
    H_INDEX = "h-index"
    I10_INDEX = "i10-index"
    CUSTOM = "custom"

class CitationSorter:
    def __init__(self):
        self.metric_weights = {
            SortMetric.CITATIONS: 1.0,
            SortMetric.H_INDEX: 1.0,
            SortMetric.I10_INDEX: 1.0
        }
    
    def set_weights(
            self,
            citations_weight: float = 1.0,
            h_index_weight: float = 1.0,
            i10_index_weight: float = 1.0
        ):
        self.metric_weights = {
            SortMetric.CITATIONS: citations_weight,
            SortMetric.H_INDEX: h_index_weight,
            SortMetric.I10_INDEX: i10_index_weight
        }
    
    def _get_metric_value(
            self, entry: dict[str, Any],
            metric: SortMetric
        ) -> float:
        try:
            stats = entry.get('statistics', {}).get('all', {})
            if metric == SortMetric.CITATIONS:
                return float(stats.get('citations', 0))
            elif metric == SortMetric.H_INDEX:
                return float(stats.get('h-index', 0))
            elif metric == SortMetric.I10_INDEX:
                return float(stats.get('i10-index', 0))
        except (ValueError, TypeError):
            return 0.0
        return 0.0
    
    def _calculate_custom_score(self, entry: dict[str, Any]) -> float:
        citations = self._get_metric_value(entry, SortMetric.CITATIONS)
        h_index = self._get_metric_value(entry, SortMetric.H_INDEX)
        i10_index = self._get_metric_value(entry, SortMetric.I10_INDEX)
        
        return (
            citations * self.metric_weights[SortMetric.CITATIONS] +
            h_index * self.metric_weights[SortMetric.H_INDEX] +
            i10_index * self.metric_weights[SortMetric.I10_INDEX]
        )
    
    def sort_entries(
            self, entries: list[dict[str, Any]],
            metric: SortMetric = SortMetric.CITATIONS, 
            reverse: bool = True
        ) -> list[dict[str, Any]]:
        if metric == SortMetric.CUSTOM:
            # sort by custom weights
            sorted_entries = sorted(
                entries,
                key=self._calculate_custom_score,
                reverse=reverse
            )
        else:
            # sort by individual metric
            sorted_entries = sorted(
                entries,
                key=lambda x: self._get_metric_value(x, metric),
                reverse=reverse
            )
        
        return sorted_entries 