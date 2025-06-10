# Projet Data Warehouse – Analyse des Avis Clients des Banques au Maroc

## Présentation Générale
Ce projet vise à centraliser, nettoyer et analyser les avis Google Maps sur les agences bancaires marocaines, afin d'extraire des insights utiles pour les décideurs : tendances de satisfaction, thématiques récurrentes, classement des agences, etc. Le pipeline s'appuie sur une stack moderne et automatisée.

---

## Spécifications et Contexte
- **Sujet** : Centraliser et valoriser les avis clients Google Maps pour les banques marocaines.
- **Objectifs principaux** :
  1. Analyser la satisfaction client (sentiment analysis)
  2. Extraire les sujets/points récurrents (topic modeling)
  3. Classer les agences selon la perception client
  4. Fournir des dashboards interactifs pour la prise de décision
- **Livrables** : Scripts Python, DAGs Airflow, modèles DBT, schéma PostgreSQL, dashboards Looker Studio, documentation complète.

---

## Stack Technique et Versions
| Composant      | Version      | Environnement |
|---------------|-------------|---------------|
| Python (Airflow) | 3.8      | airflow_venv  |
| Python (DBT)  | 3.10        | dbt_venv      |
| DBT           | 1.8.7       | dbt_venv      |
| Airflow       | 2.8.1       | airflow_venv  |
| NLP           | bert, nltk  | dbt_venv      |
| PostgreSQL    | >=15        | -             |
| BI            | Looker Studio | -           |
| Scraping      | Selenium    | airflow_venv  |

---

## Pipeline & Démarche détaillée

### 1. Collecte des données (Scraping)
- **Script principal** : `airflow/dags/scrapping.py`
- **Outils** : Selenium WebDriver, BeautifulSoup, pandas
- **Logique** :
  - Scraping automatisé des avis Google Maps pour chaque banque/ville avec Selenium
  - Gestion des popups, scrolling automatique, extraction des détails agences et avis
  - Configuration du WebDriver (Chrome/Firefox) avec options headless
  - Stockage des données brutes en JSON/CSV dans `data/`
  - Possibilité de planifier le scraping via un DAG Airflow

### 2. Ingestion dans la base (Staging)
- **Script** : `scripts/load_to_staging.py`
- **Outils** : pandas, psycopg2
- **Logique** :
  - Chargement des fichiers CSV dans la table PostgreSQL `avis_bancaires`
  - Création dynamique de la table selon les colonnes du CSV
  - Gestion des connexions et erreurs

### 3. Nettoyage et enrichissement sémantique
- **Script** : `scripts/enrich_reviews.py`
- **Outils** : pandas, transformers, nltk, spacy, torch, datasets
- **Logique** :
  - Nettoyage textuel (ponctuation, stopwords, etc.)
  - Détection de la langue
  - Analyse de sentiment (BERT, pipeline transformers)
  - Extraction de topics bancaires (pattern matching, NLP)
  - Génération d'un DataFrame enrichi, stocké dans la table `stg_avis_bancaires_enriched`

### 4. Transformation et modélisation (DBT)
- **Répertoire** : `projet_dbt/`
- **Outils** : dbt-core
- **Logique** :
  - Modèles de staging : nettoyage, enrichissement, typage des données (`models/staging/`)
  - Modèles de marts : création d'un schéma en étoile (table de faits `fact_reviews`, dimensions `dim_bank`, `dim_branch`, etc.)
  - Configuration des sources et cibles dans `dbt_project.yml` et `models/sources/sources.yml`

### 5. Visualisation et Dashboards
- **Répertoire** : `dashboards/`
- **Outils** : Looker Studio (Google Data Studio), fichiers PNG
- **Logique** :
  - Création de dashboards interactifs pour explorer :
    - Les tendances de sentiment par banque et agence
    - Les topics (sujets) les plus fréquents
    - Le classement des agences
    - Les points forts/faibles récurrents
  - Export des résultats sous forme de graphiques et visuels dans le dossier `dashboards/`
  - Les dashboards sont accessibles via Looker Studio (liens à intégrer selon votre configuration)

### 6. Orchestration et automatisation
- **Répertoire** : `airflow/`
- **Outils** : Apache Airflow
- **Logique** :
  - Un DAG Airflow orchestre toutes les étapes : scraping, ingestion, enrichissement, transformations dbt
  - Gestion des dépendances, logs, planification quotidienne/hebdomadaire

---

## Arborescence du projet
```
DW_projet/
├── airflow/           # Orchestration Airflow (DAGs, logs)
├── dashboards/        # Visualisations (ex: PNG)
├── projet_dbt/        # Projet dbt (modèles, sources, macros, ...)
└── requirements.txt
```

---

## Prérequis & Installation

### Prérequis système
- Python 3.8 (pour Airflow)
- Python 3.10 (pour DBT)
- PostgreSQL >=15
- Chrome ou Firefox (pour Selenium)
- ChromeDriver ou GeckoDriver

### 1. Création des environnements virtuels

#### Environnement Airflow (Python 3.8)
```bash
# Créer l'environnement virtuel pour Airflow
python3.8 -m venv airflow_venv

# Activer l'environnement
# Sous Windows :
airflow_venv\Scripts\activate
# Sous Linux/Mac :
source airflow_venv/bin/activate
```

#### Environnement DBT (Python 3.10)
```bash
# Créer l'environnement virtuel pour DBT
python3.10 -m venv dbt_venv

# Activer l'environnement
# Sous Windows :
dbt_venv\Scripts\activate
# Sous Linux/Mac :
source dbt_venv/bin/activate
```

### 2. Configuration Selenium
```bash
# Dans l'environnement airflow_venv
pip install selenium webdriver-manager

# Le script utilisera webdriver-manager pour télécharger automatiquement les drivers
```

### 3. Fichiers requirements

#### requirements/airflow_requirements.txt
```
apache-airflow==2.8.1
selenium==4.15.0
webdriver-manager==4.0.1
beautifulsoup4==4.12.0
pandas==1.5.3
psycopg2-binary==2.9.7
requests==2.31.0
```

#### requirements/dbt_requirements.txt
```
dbt-core==1.8.7
dbt-postgres==1.8.0
pandas==2.0.3
transformers==4.35.0
torch==2.1.0
nltk==3.8.1
spacy==3.7.0
scikit-learn==1.3.0
datasets==2.14.0
```

---

## Exécution du pipeline

### Configuration initiale
1. **Activer l'environnement Airflow**
   ```bash
   # Sous Windows :
   airflow_venv\Scripts\activate
   # Sous Linux/Mac :
   source airflow_venv/bin/activate
   ```

2. **Initialiser Airflow** (première fois uniquement)
   ```bash
   airflow db init
   airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com
   ```

### Exécution étape par étape

1. **Scraping et collecte des avis** (environnement airflow_venv)
   > ⚠️ La collecte se fait exclusivement par scraping web avec Selenium WebDriver.
   ```bash
   # Activer l'environnement Airflow
   source airflow_venv/bin/activate  # Linux/Mac
   # ou airflow_venv\Scripts\activate  # Windows
   
   python airflow/dags/scrapping.py
   # ou planifier via Airflow
   ```

2. **Chargement dans PostgreSQL** (environnement airflow_venv)
   ```bash
   python scripts/load_to_staging.py
   ```

3. **Enrichissement sémantique** (environnement dbt_venv)
   ```bash
   # Changer vers l'environnement DBT
   deactivate  # désactiver l'environnement actuel
   source dbt_venv/bin/activate  # Linux/Mac
   # ou dbt_venv\Scripts\activate  # Windows
   
   python scripts/enrich_reviews.py
   ```

4. **Transformation et modélisation dbt** (environnement dbt_venv)
   ```bash
   cd projet_dbt
   dbt run
   dbt test
   ```

5. **Orchestration complète**
   - Lancer le DAG Airflow pour automatiser tout le pipeline
   - Le DAG gérera automatiquement le basculement entre les environnements

---

## Configuration Selenium

### Options recommandées pour le WebDriver
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configuration Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # Mode sans interface graphique
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Initialisation du driver
driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=chrome_options
)
```

---

## Explications pédagogiques et bonnes pratiques
- **Scraping avec Selenium** : Utiliser des délais aléatoires, gérer les popups et implémenter une rotation des User-Agents pour éviter la détection.
- **Environnements séparés** : Maintenir des versions Python différentes pour compatibilité optimale (Airflow 3.8, DBT 3.10).
- **Nettoyage** : Toujours vérifier la qualité des données avant l'analyse NLP.
- **NLP** : Choisir des modèles adaptés à la langue (français/anglais), ajuster les patterns pour le domaine bancaire.
- **DBT** : Versionner les modèles, documenter chaque transformation, tester les modèles (`dbt test`).
- **Airflow** : Monitorer les DAGs, prévoir des alertes en cas d'échec.
- **Sécurité** : Ne jamais commiter de mots de passe ou credentials dans le code source.

---

## Auteurs
Projet réalisé par IKARNADE REDA

---

## Pour aller plus loin
- Ajouter des sources d'avis complémentaires (Trustpilot, Facebook…)
- Tester des modèles NLP plus avancés (LDA, CamemBERT…)
- Intégrer des alertes automatisées (email, Slack) via Airflow
- Déployer sur le cloud (GCP, AWS) pour mise à l'échelle
- Implémenter un système de proxy rotation pour le scraping

---

## Contact
Pour toute question, contactez : ikarnadereda@gmail.com