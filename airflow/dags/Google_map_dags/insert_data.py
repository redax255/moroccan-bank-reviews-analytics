import psycopg2
import os
import json
import glob
import datetime
from psycopg2 import sql

# Fonction pour obtenir la connexion à la base de données
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="airflow-redax",
            password="airflow_pass",
            dbname="google_map_db"
        )
        return conn
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à la base de données : {e}")
        return None

# Fonction d'insertion dans la table staging et renommage du fichier après succès
def insert_func():
    json_files = glob.glob(os.path.expanduser("~/input/data_of_json_google_map/Reviews_Of_Moroccan_Banks.json"))
    
    if not json_files:
        print("❌ Aucun fichier JSON trouvé.")
        return

    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        # DROP TABLE IF EXISTS staging;
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staging (
                bank_name VARCHAR(255),
                branch_name VARCHAR(1000),
                location VARCHAR(500),
                review_text TEXT,
                rating VARCHAR(255),
                review_date VARCHAR(255),
                scraping_date DATE
            );
        """)
        
        insertion_reussie = True  # Flag pour vérifier si l'insertion a réussi

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError as e:
                    print(f"❌ Erreur de décodage JSON : {e}")
                    insertion_reussie = False
                    continue
                
                for bank in data:
                    bank_name = bank.get("Bank_name", None)
                    for branch in bank.get("Branches", []):
                        branch_name = branch.get("branch_name", None)
                        location = branch.get("location", None)
                        
                        for review in branch.get("reviews", []):
                            review_text = review.get("review_text", None)
                            review_rating = review.get("review_rating", None)
                            review_date = review.get("review_date", None)

                            try:
                                insert_query = sql.SQL("""
                                    INSERT INTO staging (bank_name, branch_name, location, review_text, rating, review_date, scraping_date)
                                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE);
                                """)
                                cursor.execute(insert_query, (
                                    bank_name, branch_name, location, review_text, review_rating, review_date
                                ))
                            except Exception as e:
                                print(f"⚠️ Erreur lors de l'insertion d'une ligne : {e}")
                                insertion_reussie = False
                                continue

        if insertion_reussie:
            conn.commit()
            print("✅ Insertion réussie dans la table staging.")
            
            # Renommage du fichier après une insertion réussie
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{os.path.splitext(json_file)[0]}_{timestamp}.json"
            os.rename(json_file, new_filename)
            print(f"📂 Fichier renommé en : {new_filename}")

        else:
            conn.rollback()
            print("❌ Insertion échouée, aucun fichier n'a été renommé.")

    except Exception as e:
        print(f"❌ Erreur lors de l'insertion des données : {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Fonction main pour exécuter le script
def main():
    print("🚀 Début du processus d'insertion des données...")
    insert_func()
    print("✅ Processus terminé.")

# Exécution du script uniquement si c'est le fichier principal
if __name__ == "__main__":
    main()
