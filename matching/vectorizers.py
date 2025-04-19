from abc import ABC, abstractmethod

import numpy as np
from gensim.models import Word2Vec
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from sklearn.feature_extraction.text import TfidfVectorizer

from matching.preprocessors import Preprocessor


class Vectorizer(ABC):
    """
    Abstract base class for text vectorization.
    """
    @abstractmethod
    def vectorize(self, text: str) -> np.ndarray:
        """
        Convert text to vector representation.
        
        Args:
            text: Input text to vectorize
            
        Returns:
            Vector representation as numpy array
        """
        pass


class TFIDFVectorizer(Vectorizer):
    """
    Vectorizer implementation using TF-IDF.
    """
    def __init__(self, corpus: list[str]):
        self.preprocessor = Preprocessor()
        self.vectorizer = TfidfVectorizer(
            tokenizer=self.preprocessor.preprocess,
            token_pattern=None
        )
        self.vectorizer.fit(corpus)
    
    def vectorize(self, text: str) -> np.ndarray:
        """
        Convert text to TF-IDF vector.
        
        Args:
            text: Input text to vectorize
            
        Returns:
            TF-IDF vector as numpy array
        """
        return self.vectorizer.transform([text]).toarray()[0]


class Word2VecVectorizer(Vectorizer):
    """
    Vectorizer implementation using Word2Vec embeddings.
    """
    def __init__(
            self,
            corpus: list[str],
            vector_size: int = 100,
            window: int = 5,
            min_count: int = 1,
            workers: int = 4
        ):
        self.preprocessor = Preprocessor()
        processed_corpus = ([
            self.preprocessor.preprocess(doc) for doc in corpus
        ])
        
        self.model = Word2Vec(
            processed_corpus,
            vector_size=vector_size,
            window=window,
            min_count=min_count,
            workers=workers
        )
    
    def vectorize(self, text: str) -> np.ndarray:
        """
        Convert text to Word2Vec vector.
        
        Args:
            text: Input text to vectorize
            
        Returns:
            Word2Vec vector as numpy array
        """
        tokens = self.preprocessor.preprocess(text)
        
        if not tokens:
            return np.zeros(self.model.vector_size)
        
        vectors = [self.model.wv[token] for token in tokens if token in self.model.wv]
        if not vectors:
            return np.zeros(self.model.vector_size)
        return np.mean(vectors, axis=0)
