import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# download NLTK utils
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')


class Preprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
    def preprocess(self, text: str) -> list[str]:
        '''
        Preprocess text by tokenizing, removing stopwords, and cleaning.
        '''
        if not text:
            return []
        # raw -> lowercase -> alpha-numerical
        text = re.sub(r'[^\w\s]', '', text.lower())
        # tokenize
        tokens = word_tokenize(text)
        # remove stopwords and short tokens
        tokens = ([
            token for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ])
        return tokens