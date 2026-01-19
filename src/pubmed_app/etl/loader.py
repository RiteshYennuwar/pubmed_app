from typing import Optional
from dataclasses import dataclass

from pubmed_app.config import logger
from pubmed_app.database.connection import get_db_connection
from pubmed_app.etl.transformer import Article, Author

@dataclass
class LoaderStats:
    articles_inserted: int = 0
    articles_skipped: int = 0
    authors_inserted: int = 0
    journals_inserted: int = 0
    mesh_terms_inserted: int = 0

class DatabaseLoader:
    def __init__(self):
        pass

    def load(self, articles: list[Article]) -> LoaderStats:
        stats = LoaderStats()
        logger.info(f"Starting to load {len(articles)} articles into the database.")

        with get_db_connection() as conn:
            cursor = conn.cursor()

            with cursor:
                for article in articles:
                    try:
                        inserted = self._load_article(cursor, article, stats)
                        if inserted:
                            stats.articles_inserted += 1
                        else:
                            stats.articles_skipped += 1
                    except Exception as e:
                        logger.error(f"Failed to load article PMID {article.pmid}: {e}")
                        continue

        logger.info(f"Loading complete: {stats.articles_inserted} articles inserted, {stats.articles_skipped} articles skipped")

        return {
            "articles_inserted": stats.articles_inserted,
            "articles_skipped": stats.articles_skipped,
            "authors_inserted": stats.authors_inserted,
            "journals_inserted": stats.journals_inserted,
            "mesh_terms_inserted": stats.mesh_terms_inserted
        }
    
    def _load_article(self, cursor, article: Article, stats: LoaderStats) -> bool:
        cursor.execute("SELECT id FROM articles WHERE pmid = %s", (article.pmid,))
        if cursor.fetchone():
            return False

        journal_id = None
        if article.journal:
            cursor.execute("SELECT id FROM journals WHERE name = %s", (article.journal,))
            journal_row = cursor.fetchone()
            if journal_row:
                journal_id = journal_row['id']
            else:
                cursor.execute("INSERT INTO journals (name) VALUES (%s) RETURNING id", (article.journal,))
                journal_id = cursor.fetchone()['id']
                stats.journals_inserted += 1

        cursor.execute(
            """
            INSERT INTO articles (pmid, title, abstract, publication_year, journal_id)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (article.pmid, article.title, article.abstract, article.year, journal_id)
        )
        article_id = cursor.fetchone()['id']

        self._load_authors(cursor, article_id, article.authors, stats)
        self._load_mesh_terms(cursor, article_id, article.mesh_terms, stats)

        return True
    
    def _get_or_create_journal(self, cursor, journal_name: str, stats: LoaderStats) -> int:
        cursor.execute("SELECT id FROM journals WHERE name = %s", (journal_name,))
        row = cursor.fetchone()
        if row:
            return row['id']
        
        cursor.execute("INSERT INTO journals (name) VALUES (%s) RETURNING id", (journal_name,))
        journal_id = cursor.fetchone()['id']
        stats.journals_inserted += 1
        return journal_id
    
    def _load_authors(self, cursor, article_id: int, authors: list[Author], stats: LoaderStats) -> None:
        for position, author in enumerate(authors, start=1):
            cursor.execute(
                "SELECT id FROM authors WHERE last_name = %s AND first_name = %s",
                (author.last_name, author.fore_name)
            )
            author_row = cursor.fetchone()
            if author_row:
                author_id = author_row['id']
            else:
                cursor.execute(
                    "INSERT INTO authors (last_name, first_name) VALUES (%s, %s) RETURNING id",
                    (author.last_name, author.fore_name)
                )
                author_id = cursor.fetchone()['id']
                stats.authors_inserted += 1

            cursor.execute(
                "INSERT INTO article_authors (article_id, author_id, author_postion) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (article_id, author_id, position)
            )

    def _load_mesh_terms(self, cursor, article_id: int, mesh_terms: list[str], stats: LoaderStats) -> None:
        for term in mesh_terms:
            cursor.execute("SELECT id FROM mesh_terms WHERE term = %s", (term,))
            mesh_row = cursor.fetchone()
            if mesh_row:
                mesh_id = mesh_row['id']
            else:
                cursor.execute("INSERT INTO mesh_terms (term) VALUES (%s) RETURNING id", (term,))
                mesh_id = cursor.fetchone()['id']
                stats.mesh_terms_inserted += 1

            cursor.execute(
                "INSERT INTO article_mesh_terms (article_id, mesh_term_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (article_id, mesh_id)
            )