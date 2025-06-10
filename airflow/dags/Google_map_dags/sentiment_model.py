# Google_map_dags/sentiment_model.py
import logging
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        logging.info("Chargement du pipeline sentiment-analysis…")
        _pipeline = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )
    return _pipeline

def classify_sentiment(text):
    pipe = get_pipeline()
    try:
        result = pipe(text)
        label = result[0]["label"]
        if label in ("5 stars", "4 stars"):
            return "Positive"
        if label in ("1 star", "2 stars"):
            return "Negative"
        return "Neutral"
    except Exception as e:
        logging.error(f"Erreur classification sentiment : {e}")
        return "Neutral"


print(classify_sentiment('very good service'))