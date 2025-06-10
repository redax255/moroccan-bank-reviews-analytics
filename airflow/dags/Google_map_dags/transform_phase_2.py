"""
Transform Phase 2: Sentiment Analysis and Language Detection for Google Maps Reviews
"""
import pandas as pd
from sqlalchemy import create_engine
from langdetect import detect
import nltk
from nltk.corpus import stopwords
import string
import gensim
import logging

# Import our custom sentiment module
from Google_map_dags.sentiment_model import classify_sentiment

logging.basicConfig(level=logging.INFO)

# Make sure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Function to detect language
def detect_language(text):
    """
    Detect the language of a text
    
    Args:
        text (str): Text to analyze
        
    Returns:
        str: Language code or None if detection fails
    """
    if not text or not isinstance(text, str):
        return None
        
    try:
        return detect(text)
    except Exception as e:
        logging.error(f"Language detection error: {e}")
        return None  # In case the language detection fails

# Function to preprocess text (tokenization, removing stopwords and punctuation)
stop_words = set(stopwords.words('french'))

def preprocess(text):
    """Preprocess text for topic modeling"""
    if not text or not isinstance(text, str):
        return []
        
    try:    
        tokens = nltk.word_tokenize(text.lower())  # Lowercase and tokenize
        tokens = [word for word in tokens if word not in stop_words]  # Remove stopwords
        tokens = [word for word in tokens if word not in string.punctuation]  # Remove punctuation
        return tokens
    except Exception as e:
        logging.error(f"Text preprocessing error: {e}")
        return []

# Function to extract common topics using LDA from all reviews
def extract_common_topics(reviews, n_topics=5):
    """
    Extract common topics from a list of reviews using LDA
    
    Args:
        reviews (list): List of review texts
        n_topics (int): Number of topics to extract
        
    Returns:
        list: List of topic words
    """
    if not reviews or len(reviews) < 10:  # Need sufficient data for meaningful topics
        logging.warning("Not enough reviews for topic modeling")
        return []
        
    try:
        # Preprocess all reviews
        preprocessed_reviews = [preprocess(review) for review in reviews if review]
        preprocessed_reviews = [review for review in preprocessed_reviews if review]  # Remove empty lists
        
        if not preprocessed_reviews:
            logging.warning("No valid preprocessed reviews for topic modeling")
            return []
            
        # Create a dictionary and corpus
        dictionary = gensim.corpora.Dictionary(preprocessed_reviews)
        corpus = [dictionary.doc2bow(text) for text in preprocessed_reviews]
        
        # Apply LDA for topic modeling
        lda = gensim.models.LdaModel(corpus, num_topics=n_topics, id2word=dictionary, 
                                     passes=15, alpha='auto', eta='auto')

        # Extract common topics using show_topics()
        topics = lda.show_topics(num_topics=n_topics, num_words=5, formatted=True)
        
        # Process the topics and extract the top words for each topic
        topic_words = []
        for topic in topics:
            topic_words.append([word for word, prob in lda.show_topic(topic[0], topn=5)])
        
        return topic_words
    except Exception as e:
        logging.error(f"Topic extraction error: {e}")
        return []

def column_exists(connection, table_name, column_name):
    """
    Check if a column exists in the given table.
    
    Args:
        connection: Database connection
        table_name (str): Table name
        column_name (str): Column name
        
    Returns:
        bool: True if column exists, False otherwise
    """
    query = f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{table_name}' AND column_name = '{column_name}';
    """
    result = connection.execute(query).fetchall()
    return len(result) > 0

# Main function
def main():
    """Main function to process reviews with sentiment analysis and language detection"""
    logging.info("Starting transform phase 2...")
    
    try:
        # Connect to PostgreSQL
        db_engine = create_engine('postgresql://airflow-redax:airflow_pass@localhost:5432/google_map_db')
        connection = db_engine.connect()
        logging.info("Connected to database")
        
        # Check if the 'language' and 'sentiment' columns exist in 'cleaned_reviews' table
        if not column_exists(connection, 'cleaned_reviews', 'language'):
            connection.execute("ALTER TABLE public.cleaned_reviews ADD COLUMN language VARCHAR(10);")
            logging.info("Added 'language' column.")

        if not column_exists(connection, 'cleaned_reviews', 'sentiment'):
            connection.execute("ALTER TABLE public.cleaned_reviews ADD COLUMN sentiment VARCHAR(50);")
            logging.info("Added 'sentiment' column.")
            
        # Fetch data from cleaned_reviews
        query = "SELECT bank_name, branch_name, location, review_text, rating, review_date FROM cleaned_reviews;"
        df = pd.read_sql(query, connection)
        logging.info(f"Fetched {len(df)} reviews from database")

        # Apply language detection and sentiment analysis
        df['language'] = df['review_text'].apply(detect_language)
        df['sentiment'] = df['review_text'].apply(classify_sentiment)
        logging.info("Applied language detection and sentiment analysis")

        # Langues supportées par le modèle
        supported_languages = ['en', 'nl', 'de', 'fr', 'it', 'es']

        # Filter reviews by supported languages
        df_filtered = df[df['language'].isin(supported_languages)]
        logging.info(f"Filtered to {len(df_filtered)} reviews in supported languages")

        # Extract common topics from all reviews
        try:
            if len(df_filtered) > 0:
                common_topics = extract_common_topics(df_filtered['review_text'].tolist(), n_topics=5)
                logging.info(f"Topics extraction complete: {common_topics}")
            else:
                logging.warning("No reviews to extract topics from")
        except Exception as e:
            logging.error(f"Error during topic extraction: {e}")

        # Update the existing cleaned_reviews table with sentiment and language
        update_count = 0
        for index, row in df_filtered.iterrows():
            update_query = """
            UPDATE cleaned_reviews
                SET language = %s, sentiment = %s
                WHERE bank_name = %s AND branch_name = %s AND location = %s AND review_text = %s;
            """
            connection.execute(update_query, (row['language'], row['sentiment'], 
                                              row['bank_name'], row['branch_name'], 
                                              row['location'], row['review_text']))
            update_count += 1
            
            # Log progress every 100 updates
            if update_count % 100 == 0:
                logging.info(f"Updated {update_count}/{len(df_filtered)} reviews")
                
        logging.info(f"Updated sentiment and language for {update_count} reviews")

        connection.close()
        logging.info("Transform phase 2 completed successfully")
        
    except Exception as e:
        logging.error(f"Transform phase 2 failed: {e}")
        raise

if __name__ == "__main__":
    main()