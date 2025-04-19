from abc import ABC, abstractmethod

import json
import numpy as np
from typing import Any

from matching.preprocessors import Preprocessor
from matching.vectorizers import (
    TFIDFVectorizer, Word2VecVectorizer
)
from .sorters import CitationSorter, SortMetric


NUM_MATCHES: int = 10


class Matcher(ABC):
    """
    Abstract base class for implementing different matching algorithms.
    Provides common functionality for processing and matching research areas.
    """
    def __init__(
            self, data_path: str = 'public/results.json'
        ):
        with open(data_path, 'r') as f:
            self.data = json.load(f)
        self.preprocessor = Preprocessor()
        self.vectorizer = None
        self.citation_sorter = CitationSorter()
    
    @abstractmethod
    def get_matches(
            self, query: str = '', N: int = NUM_MATCHES
        ) -> list[dict[str, Any]]:
        """
        Get matches for a given query.
        
        Args:
            query: Search query string
            N: Number of matches to return
            
        Returns:
            List of matched professor entries
        """
        pass

    def _get_research_areas_text(
            self, entry: dict[str, Any]
        ) -> str:
        """
        Extract and format research areas from an entry.
        
        Args:
            entry: Professor data entry
            
        Returns:
            Formatted string of research areas
        """
        research_areas = entry.get('research_areas', [])
        
        if (
            not research_areas
            or
            not isinstance(research_areas, (list, tuple))
        ):
            return ''
        return ' '.join(
            str(area) for area in research_areas if area
        )


class TFIDFMatcher(Matcher):
    """
    Matcher implementation using TF-IDF vectorization.
    """
    def __init__(
            self, data_path: str = 'public/results.json'
        ):
        super().__init__(data_path)
        corpus = ([
            self._get_research_areas_text(entry) for entry in self.data
        ])
        self.vectorizer = TFIDFVectorizer(corpus)
        self.entry_vectors = {
            i: self.vectorizer.vectorize(
                self._get_research_areas_text(entry)
            ) for i, entry in enumerate(self.data)
        }
    
    def get_matches(
            self, query: str = '',
            N: int = NUM_MATCHES, 
            sort_by: SortMetric = None, 
            sort_reverse: bool = True
        ) -> list[dict[str, Any]]:
        """
        Get matches using TF-IDF similarity.
        
        Args:
            query: Search query string
            N: Number of matches to return
            sort_by: Metric to sort results by
            sort_reverse: Whether to sort in descending order
            
        Returns:
            List of matched professor entries
        """
        if not query:
            return self.data[:N]
        else:
            query_vector = self.vectorizer.vectorize(query)
            similarities = []
            for i, entry_vector in self.entry_vectors.items():
                if np.any(entry_vector):
                    similarity = np.dot(query_vector, entry_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(entry_vector)
                    )
                    similarities.append((i, similarity))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = [i for i, _ in similarities[:N]]
            matches = [self.data[i] for i in top_indices]
        
        if sort_by is not None:
            matches = self.citation_sorter.sort_entries(
                matches, sort_by, sort_reverse
            )
        
        return matches


class Word2VecMatcher(Matcher):
    """
    Matcher implementation using Word2Vec embeddings.
    """
    def __init__(
            self, data_path: str = 'public/results.json'
        ):
        super().__init__(data_path)
        corpus = ([
            self._get_research_areas_text(entry) for entry in self.data
        ])
        self.vectorizer = Word2VecVectorizer(corpus)
        self.entry_vectors = {
            i: self.vectorizer.vectorize(self._get_research_areas_text(entry))
            for i, entry in enumerate(self.data)
        }
    
    def get_matches(
            self, query: str = '',
            N: int = NUM_MATCHES,
            sort_by: SortMetric = None, 
            sort_reverse: bool = True
        ) -> list[dict[str, Any]]:
        """
        Get matches using Word2Vec similarity.
        
        Args:
            query: Search query string
            N: Number of matches to return
            sort_by: Metric to sort results by
            sort_reverse: Whether to sort in descending order
            
        Returns:
            List of matched professor entries
        """
        if not query:
            return self.data[:N]
        else:
            query_vector = self.vectorizer.vectorize(query)
            similarities = []
            for i, entry_vector in self.entry_vectors.items():
                if np.any(entry_vector):
                    similarity = np.dot(query_vector, entry_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(entry_vector)
                    )
                    similarities.append((i, similarity))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = [i for i, _ in similarities[:N]]
            matches = [self.data[i] for i in top_indices]
        
        if sort_by is not None:
            matches = self.citation_sorter.sort_entries(
                matches, sort_by, sort_reverse
            )
        
        return matches