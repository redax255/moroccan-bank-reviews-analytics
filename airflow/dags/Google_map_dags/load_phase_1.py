import psycopg2

def get_db_connection():
    """Établit une connexion avec PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="azerty",
            dbname="Data_Warehouse_Project"
        )
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données : {e}")
        return None

def setup_schema():
    """Crée le schéma 'Decisionnelle' s'il n'existe pas."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS Decisionnelle;")
                conn.commit()
                print("✅ Schéma 'Decisionnelle' créé avec succès.")
        except Exception as e:
            print(f"❌ Erreur lors de la création du schéma : {e}")
        finally:
            conn.close()

def create_tables():
    """Crée les tables du modèle en étoile dans 'Decisionnelle'."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS Decisionnelle.dim_bank (
                    bank_id SERIAL PRIMARY KEY,
                    bank_name VARCHAR(255) UNIQUE NOT NULL
                );
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS Decisionnelle.dim_branch (
                    branch_id SERIAL PRIMARY KEY,
                    branch_name TEXT UNIQUE NOT NULL,
                    bank_id INT REFERENCES Decisionnelle.dim_bank(bank_id)
                );
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS Decisionnelle.dim_location (
                    location_id SERIAL PRIMARY KEY,
                    location TEXT UNIQUE NOT NULL
                );
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS Decisionnelle.dim_sentiment (
                    sentiment_id SERIAL PRIMARY KEY,
                    sentiment_label VARCHAR(50) UNIQUE NOT NULL
                );
                """)

                cur.execute("""
                CREATE TABLE IF NOT EXISTS Decisionnelle.fact_reviews (
                    review_id SERIAL PRIMARY KEY,
                    bank_id INT REFERENCES Decisionnelle.dim_bank(bank_id),
                    branch_id INT REFERENCES Decisionnelle.dim_branch(branch_id),
                    location_id INT REFERENCES Decisionnelle.dim_location(location_id),
                    sentiment_id INT REFERENCES Decisionnelle.dim_sentiment(sentiment_id),
                    review_text TEXT NOT NULL,
                    rating INT NOT NULL,
                    review_date NUMERIC NOT NULL,
                    language VARCHAR(10)
                );
                """)

                conn.commit()
                print("✅ Tables créées avec succès dans 'Decisionnelle'.")
        except Exception as e:
            print(f"❌ Erreur lors de la création des tables : {e}")
        finally:
            conn.close()

def main():
    """Exécute la création du schéma et des tables."""
    setup_schema()
    create_tables()

if __name__ == "__main__":
    main()
