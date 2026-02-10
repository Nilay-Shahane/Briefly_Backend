import os
import spacy
from collections import Counter
from heapq import nlargest
nlp = None
def load_model():
    print('-- Loading Spacy Model (Static) --')
    try:
        nlp = spacy.load('en_core_web_sm')
        print('Spacy Model loaded')
    except OSError:
        print('WARNING: Spacy model not found. Run: python -m spacy download en_core_web_sm')

def predict(self, text: str, num_sentences: int) -> str:
        if not self.nlp: 
            self.load()
            if not self.nlp:
                return "Error: Static model not loaded."
        
        doc = self.nlp(text)
        
        keywords = [
            token.text.lower() for token in doc
            if not token.is_stop and not token.is_punct and token.text != '\n'
        ]
        word_freq = Counter(keywords)
        
        if not word_freq: return "Text too short to summarize."

        max_freq = max(word_freq.values())
        for word in word_freq:
            word_freq[word] = word_freq[word] / max_freq

        sent_score = {}
        for sent in doc.sents:
            for word in sent.text.split():
                if word.lower() in word_freq:
                    if sent in sent_score:
                        sent_score[sent] += word_freq[word.lower()]
                    else:
                        sent_score[sent] = word_freq[word.lower()]
        
        top_sentences = nlargest(num_sentences, sent_score, key=sent_score.get)
        final_summary = ' '.join([sent.text for sent in top_sentences])
        return final_summary