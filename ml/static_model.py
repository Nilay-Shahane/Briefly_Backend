import spacy
from collections import Counter
from heapq import nlargest

nlp = None

def load_model():
    global nlp
    print('-- Loading Spacy Model (Static) --')
    try:
        nlp = spacy.load('en_core_web_sm')
        print('Spacy Model loaded')
    except OSError:
        print('WARNING: Spacy model not found.')

def predict(text: str, num_sentences: int) -> str:
    global nlp

    if not nlp:
        load_model()
        if not nlp:
            return "Error: Static model not loaded."

    doc = nlp(text)

    keywords = [
        token.text.lower()
        for token in doc
        if not token.is_stop and not token.is_punct and token.text != '\n'
    ]

    word_freq = Counter(keywords)

    if not word_freq:
        return "Text too short to summarize."

    max_freq = max(word_freq.values())

    for word in word_freq:
        word_freq[word] /= max_freq

    sent_score = {}

    for sent in doc.sents:
        for token in sent:
            if token.text.lower() in word_freq:
                sent_score[sent] = sent_score.get(sent, 0) + word_freq[token.text.lower()]

    top_sentences = nlargest(num_sentences, sent_score, key=sent_score.get)
    top_sentences = sorted(top_sentences, key=lambda sent: sent.start)

    return " ".join([sent.text for sent in top_sentences])
