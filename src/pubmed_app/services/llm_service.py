import re
from typing import Optional

from pubmed_app.config import logger, settings
from pubmed_app.database import execute_query

DB_SCHEMA = """
    TABLES:
    - articles (id, pmid, title, abstract, publication_year, journal_id)
    - authors (id, last_name, fore_name, initials)
    - journals (id, name)
    - mesh_terms (id, term)
    - article_authors (article_id, author_id, author_position)
    - article_mesh_terms (article_id, mesh_term_id)
    """

class LLMService:
    BASE_URL: str = settings.BASE_URL

    def __init__(self):
        self.client = None
        self.model = settings.LLM_MODEL_NAME
        self._init_client()

    def _init_client(self):
        if settings.API_KEY:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=settings.API_KEY,
                    base_url=self.BASE_URL
                )

                logger.info("Initialized OpenAI client successfully.")
            except ImportError as e:
                logger.error("Failed to initialize client: {e}")
                self.client = None
        else:
            logger.warning("API_KEY not set in settings. LLM client not initialized.")

    def is_available(self) -> bool:
        return self.client is not None
    
    def text_to_sql(self, question: str) -> Optional[str]:
        if not self.is_available():
            logger.error("LLM client is not available.")
            return None
        
        prompt = f"""You are a SQL expert. Convert natural language questions to PostgreSQL queries.

                    Database Schema:
                    {DB_SCHEMA}

                    Rules:
                    1. Return ONLY the SQL query, no explanations or markdown
                    2. Use proper JOINs for related tables
                    3. Always use ILIKE for text searches (case-insensitive)
                    4. Limit results to 100 unless specified
                    5. Only SELECT queries are allowed (no INSERT, UPDATE, DELETE)
                    6. For full-text search on title/abstract, use: 
                       to_tsvector('english', title) @@ plainto_tsquery('english', 'search terms')

                    Examples:
                    Q: How many articles are there?
                    A: SELECT COUNT(*) as count FROM articles;

                    Q: Find articles about cancer from 2023
                    A: SELECT a.pmid, a.title, a.publication_year 
                       FROM articles a 
                       WHERE to_tsvector('english', a.title || ' ' || COALESCE(a.abstract, '')) @@ plainto_tsquery('english', 'cancer')
                       AND a.publication_year = 2023
                       LIMIT 100;

                    Q: Which journals have the most articles?
                    A: SELECT j.name, COUNT(*) as article_count 
                       FROM journals j 
                       JOIN articles a ON a.journal_id = j.id 
                       GROUP BY j.name 
                       ORDER BY article_count DESC 
                       LIMIT 10;

                    Q: Find articles by author Smith
                    A: SELECT a.pmid, a.title, au.last_name, au.first_name
                       FROM articles a
                       JOIN article_authors aa ON a.id = aa.article_id
                       JOIN authors au ON aa.author_id = au.id
                       WHERE au.last_name ILIKE '%Smith%'
                       LIMIT 100;
                    """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0
            )

            sql_query = response.choices[0].message.content.strip()

            sql_query = re.sub(r'^```sql\s*', '', sql_query)
            sql_query = re.sub(r'\s*```$', '', sql_query)
            sql_query = re.sub(r'\s*```$', '', sql_query)
            sql_query = sql_query.strip()

            logger.info(f"Generated SQL query: {sql_query[:100]}...")
            return sql_query
        
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return None
    
    def ask(self, question: str) -> dict:
        result = {
            "question": question,
            "sql_query": None,
            "results": None,
            "error": None
        }

        sql_query = self.text_to_sql(question)

        if not sql_query:
            result["error"] = "Failed to generate SQL query."
            return result
        
        result["sql_query"] = sql_query

        if not sql_query.lower().startswith("select"):
            result["error"] = "Generated SQL query is not a SELECT statement."
            return result
        
        try:
            results = execute_query(sql_query)
            result["results"] = results
            logger.info(f"Query executed successfully, retrieved {len(results)} records.")
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            result["error"] = f"Error executing SQL query: {e}"

        return result
    
    def get_model_info(self) -> Optional[dict]:
        return {
            "model_name": self.model,
            "base_url": self.BASE_URL,
            "available": self.is_available()
        }