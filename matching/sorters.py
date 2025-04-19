from typing import Any, Callable
from enum import Enum
import numpy as np

class SortMetric(Enum):
    """
    Enumeration of available sorting metrics for professor entries.
    """
    CITATIONS = "citations"
    H_INDEX = "h-index"
    I10_INDEX = "i10-index"
    CUSTOM = "custom"

class CitationSorter:
    """
    Utility class for sorting professor entries based on citation metrics.
    """
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
        """
        Set custom weights for citation metrics.
        
        Args:
            citations_weight: Weight for total citations
            h_index_weight: Weight for h-index
            i10_index_weight: Weight for i10-index
        """
        self.metric_weights = {
            SortMetric.CITATIONS: citations_weight,
            SortMetric.H_INDEX: h_index_weight,
            SortMetric.I10_INDEX: i10_index_weight
        }
    
    def _get_metric_value(
            self, entry: dict[str, Any],
            metric: SortMetric
        ) -> float:
        """
        Extract metric value from professor entry.
        
        Args:
            entry: Professor data entry
            metric: Metric to extract
            
        Returns:
            Extracted metric value as float
        """
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
        """
        Calculate weighted score using all citation metrics.
        
        Args:
            entry: Professor data entry
            
        Returns:
            Weighted score as float
        """
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
        """
        Sort professor entries by specified metric.
        
        Args:
            entries: List of professor entries
            metric: Metric to sort by
            reverse: Whether to sort in descending order
            
        Returns:
            Sorted list of professor entries
        """
        if metric == SortMetric.CUSTOM:
            sorted_entries = sorted(
                entries,
                key=self._calculate_custom_score,
                reverse=reverse
            )
        else:
            sorted_entries = sorted(
                entries,
                key=lambda x: self._get_metric_value(x, metric),
                reverse=reverse
            )
        
        return sorted_entries 