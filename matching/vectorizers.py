from abc import ABC, abstractmethod

import numpy as np
from gensim.models import Word2Vec
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from sklearn.feature_extraction.text import TfidfVectorizer

from matching.preprocessors import Preprocessor


class Vectorizer(ABC):
    @abstractmethod
    def vectorize(self, text: str) -> np.ndarray:
        pass


class TFIDFVectorizer(Vectorizer):
    def __init__(self, corpus: list[str]):
        self.preprocessor = Preprocessor()
        self.vectorizer = TfidfVectorizer(
            tokenizer=self.preprocessor.preprocess,
            token_pattern=None
        )
        self.vectorizer.fit(corpus)
    
    def vectorize(self, text: str) -> np.ndarray:
        return self.vectorizer.transform([text]).toarray()[0]


class Word2VecVectorizer(Vectorizer):
    def __init__(
            self,
            corpus: list[str],
            vector_size: int = 100,
            window: int = 5,
            min_count: int = 1,
            workers: int = 4
        ):
        self.preprocessor = Preprocessor()
        # preprocess all documents
        processed_corpus = ([
            self.preprocessor.preprocess(doc) for doc in corpus
        ])
        
        # train word2vec model
        self.model = Word2Vec(
            processed_corpus,
            vector_size=vector_size,
            window=window,
            min_count=min_count,
            workers=workers
        )
    
    def vectorize(self, text: str) -> np.ndarray:
        tokens = self.preprocessor.preprocess(text)
        
        if not tokens:
            return np.zeros(self.model.vector_size)
        
        # average word vectors
        vectors = [self.model.wv[token] for token in tokens if token in self.model.wv]
        if not vectors:
            return np.zeros(self.model.vector_size)
        return np.mean(vectors, axis=0)
