# PubMed Research Explorer

A full-stack application for exploring PubMed research articles with ETL pipeline, PostgreSQL storage, and Streamlit UI.

## Features

- **ETL Pipeline**: Fetch articles from PubMed API and store in PostgreSQL
- **Search**: Filter articles by keyword, year, journal, author, MeSH terms
- **Article Details**: View full article information with authors and MeSH terms
- **Q&A**: Ask questions in natural language (powered by Groq LLM)
- **Export**: Download results as CSV or JSON

## Tech Stack

- **Python 3.10+**
- **PostgreSQL** - Database
- **Streamlit** - Web interface
- **Typer** - CLI framework
- **Groq** - LLM for natural language queries
- **PubMed E-utilities** - Data source

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/RiteshYennuwar/pubmed_app.git
cd pubmed_app
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
# On Linux: source venv/bin/activate
```

### 3. Install the package

```bash
pip install -e .
```

### 4. Setup PostgreSQL

Install PostgreSQL and initialize.

from here https://www.postgresql.org/download/

### 5. Configure environment variables

Create a `.env` file in the project root:

```bash
PUBMED_EMAIL=your@email.com
PUBMED_API_KEY=your_api_key_here

DB_HOST=localhost
DB_PORT=5432
DB_NAME=pubmed_db
DB_USER=postgres
DB_PASSWORD=your_password_here

BASE_URL=base_url_here
LLM_MODEL_NAME=model_name_here
API_KEY=api_key_here
```

### 6. Initialize database

```bash
python -m pubmed_app db init
```

### 7. Load data from PubMed

```bash
python -m pubmed_app etl --topic "machine learning medicine" --max-results 100
```

### 8. Run the application

```bash
python -m pubmed_app serve
```

Open http://localhost:8501 in your browser.