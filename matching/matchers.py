import os
import re
import json
import numpy as np
from typing import Any
from openai import OpenAI
from abc import ABC, abstractmethod

from matching.preprocessors import Preprocessor
from matching.vectorizers import (
    TFIDFVectorizer, Word2VecVectorizer
)
from .sorters import CitationSorter, SortMetric
from dashboard.monitor import monitor_matching


NUM_MATCHES: int = 10
MAX_TOKENS: int = 150
TEMPERATURE: float = 0.2
PROMPT_RESEARCHER_LIMIT: int = 100
DATA_PATH: str = 'public/results.json'


class Matcher(ABC):
    def __init__(
            self, data_path: str = DATA_PATH
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
        pass

    def _get_research_areas_text(
            self, entry: dict[str, Any]
        ) -> str:
        '''
        Extract and format research areas from an entry.
        '''
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
    
    def _format_researcher_list_for_prompt(
            self, max_entries: int = PROMPT_RESEARCHER_LIMIT
        ) -> str:
        '''
        Formats a subset of researcher data for the LLM prompt.
        '''
        formatted_list = []
        
        # limit entries to avoid excess prompt length
        entries_to_format = self.data[:max_entries]
        for i, entry in enumerate(entries_to_format):
            name = entry.get('name', f'Researcher {i+1}')
            areas = self._get_research_areas_text(entry)
            if areas:
                formatted_list.append(f'- {name}: {areas}')
            else:
                formatted_list.append(f'- {name}: (No listed research areas)')
        
        # put marker if truncated
        if len(self.data) > max_entries:
            formatted_list.append(
                f'\n... and {len(self.data) - max_entries} more researchers.'
            )
        
        return '\n'.join(formatted_list)


class TFIDFMatcher(Matcher):
    def __init__(
            self, data_path: str = DATA_PATH
        ):
        super().__init__(data_path)
        # prepare corpus from research areas
        corpus = ([
            self._get_research_areas_text(entry) for entry in self.data
        ])
        self.vectorizer = TFIDFVectorizer(corpus)
        # pre-compute vectors for all entries
        self.entry_vectors = {
            i: self.vectorizer.vectorize(
                self._get_research_areas_text(entry)
            ) for i, entry in enumerate(self.data)
        }
    
    @monitor_matching('TF-IDF')
    def get_matches(
            self, query: str = '',
            N: int = NUM_MATCHES, 
            sort_by: SortMetric = None, 
            sort_reverse: bool = True
        ) -> list[dict[str, Any]]:
        if not query:
            return self.data[:N]
        else:
            query_vector = self.vectorizer.vectorize(query)
            # calculate cosine similarity
            similarities = []
            for i, entry_vector in self.entry_vectors.items():
                if np.any(entry_vector):  # ckip entries with no research areas
                    similarity = np.dot(query_vector, entry_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(entry_vector)
                    )
                    similarities.append((i, similarity))
            
            # sort by similarity and get top N
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = [i for i, _ in similarities[:N]]
            matches = [self.data[i] for i in top_indices]
        
        # citation sorting if tie
        if sort_by is not None:
            matches = self.citation_sorter.sort_entries(
                matches, sort_by, sort_reverse
            )
        
        return matches


class Word2VecMatcher(Matcher):
    def __init__(
            self, data_path: str = DATA_PATH
        ):
        super().__init__(data_path)
        # prepare corpus from research areas
        corpus = ([
            self._get_research_areas_text(entry) for entry in self.data
        ])
        self.vectorizer = Word2VecVectorizer(corpus)
        # pre-compute vectors for all entries
        self.entry_vectors = {
            i: self.vectorizer.vectorize(self._get_research_areas_text(entry))
            for i, entry in enumerate(self.data)
        }
    
    @monitor_matching('Word2Vec')
    def get_matches(
            self, query: str = '',
            N: int = NUM_MATCHES,
            sort_by: SortMetric = None, 
            sort_reverse: bool = True
        ) -> list[dict[str, Any]]:
        if not query:
            return self.data[:N]
        else:
            query_vector = self.vectorizer.vectorize(query)
            # calculate cosine similarity
            similarities = []
            for i, entry_vector in self.entry_vectors.items():
                if np.any(entry_vector):  # skip entries with no research areas
                    similarity = np.dot(query_vector, entry_vector) / (
                        (np.linalg.norm(query_vector) * np.linalg.norm(entry_vector))
                        + 1e-3
                    )
                    similarities.append((i, similarity))
            
            # sort by similarity and get top N
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = [i for i, _ in similarities[:N]]
            matches = [self.data[i] for i in top_indices]
        
        # citation sorting if tie
        if sort_by is not None:
            matches = self.citation_sorter.sort_entries(
                matches, sort_by, sort_reverse
            )
        
        return matches


class KeywordMatcher(Matcher):
    def __init__(
            self, data_path: str = DATA_PATH
        ):
        super().__init__(data_path)
        
        # pre-compute research areas per entry
        self.entry_keywords = {}
        for i, entry in enumerate(self.data):
            text = self._get_research_areas_text(entry)
            processed_text = self.preprocessor.preprocess(text)
            self.entry_keywords[i] = set(processed_text)

    @monitor_matching('KeywordMatch')
    def get_matches(
        self,
        query: str | list[str] = '',
        N: int = NUM_MATCHES,
        sort_by: SortMetric = None,
        sort_reverse: bool = True
    ) -> list[dict[str, Any]]:
        
        if isinstance(query, list):
            query_text = ' '.join(query)
        else:
            query_text = query

        if not query_text:
            # query empty -> return top N sorted (if specified)
            if sort_by is not None:
                return self.citation_sorter.sort_entries(
                    self.data, sort_by, sort_reverse
                )[:N]
            else:
                return self.data[:N]

        processed_query = self.preprocessor.preprocess(query_text)
        query_keywords = set(processed_query)

        if not query_keywords:
             return [] # no-match found

        # socre with key-word overlap
        scores = []
        for i, entry_keyword_set in self.entry_keywords.items():
            overlap = len(
                query_keywords.intersection(entry_keyword_set)
            )
            if overlap > 0: # has to have at least one match
                scores.append((i, overlap))
        
        # sort by overlap score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # select top N
        top_indices = [i for i, _ in scores[:N]]
        matches = [self.data[i] for i in top_indices]
        
        # citation sorting if tie
        if sort_by is not None:
            matches = self.citation_sorter.sort_entries(
                matches, sort_by, sort_reverse
            )
        
        return matches


class DeepseekMatcher(Matcher):
    def __init__(
            self, data_path: str = DATA_PATH
        ):
        super().__init__(data_path)
        self.client = OpenAI(
            api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url='https://api.deepseek.com'
        )

    @monitor_matching('DeepseekLLM')
    def get_matches(
        self,
        query: str = '',
        N: int = NUM_MATCHES,
        sort_by: SortMetric = None,
        sort_reverse: bool = True
    ) -> list[dict[str, Any]]:
        if not query:
            print(
                'DeepseekMatcher requires a query.'
            )
            return []
        if not self.client:
            print(
                'Deepseek client not initialized. Cannot get matches.'
            )
            return []

        # format list of researchers to make prompt
        researcher_context = self._format_researcher_list_for_prompt(
            max_entries=PROMPT_RESEARCHER_LIMIT
        )

        prompt = (
            f'Here is a list of researchers and their research areas:\n\n'
            f'{researcher_context}\n\n'
            f'Based ONLY on this provided list identify names of top {N} researchers '
            f'whose research areas are most relevant to the following query: "{query}".\n\n'
            f'List only names separated by commas.'
        )

        try:
            response = self.client.chat.completions.create(
                model='deepseek-chat',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an AI assistant helping match researchers to queries based on their research areas.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )
            
            # extract names from response
            content = response.choices[0].message.content
            matched_names = ([
                name.strip() for name in content.split(',') if name.strip()
            ])
            
            if not matched_names:
                print(
                    f'DeepseekMatcher: LLM did not return any names for query "{query}".'
                )
                return []

            # retrieve data for given names
            name_to_entry = {
                entry.get('name'): entry for entry in self.data
            }
            matches = ([
                name_to_entry[name] for name in matched_names if name in name_to_entry
            ])
            
            if len(matches) < N and len(matches) < len(self.data):
                print(
                    f'Found only {len(matches)}/{N} requested researchers matching LLM output.'
                    )

        except Exception as e:
            print(
                f'Error calling Deepseek API or parsing response: {e}'
            )
            return []

        # citation sorting if tie
        if sort_by is not None:
            matches = self.citation_sorter.sort_entries(
                matches, sort_by, sort_reverse
            )

        return matches[:N]
