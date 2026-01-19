from pubmed_app.config import settings, logger
from pubmed_app.database.connection import (
    execute_query,
    execute_single_query,
    get_dict_cursor
)

from pubmed_app.database.models import Article, Author

from typing import Optional

class ArticleCRUD:
    def get_by_pmid(self, pmid: str) -> Article | None:
        row = execute_single_query(
            (pmid,)
        )

        if not row:
            return None
        
        article = self._row_to_article(row)
        article.authors = self._get_authors_for_article(article.pmid)
        article.mesh_terms = self._get_mesh_terms_for_article(article.pmid)
        return article
    
    def get_by_id(self, article_id: int) -> Optional[Article]:
        row = execute_single_query(
            """
            SELECT 
                a.id, a.pmid, a.title, a.abstract, a.publication_year,
                j.name AS journal_name
            FROM articles a
            LEFT JOIN journals j ON a.journal_id = j.id
            WHERE a.id = %s
            """,
            (article_id,)
        )

        if not row:
            return None
        
        article = self._row_to_article(row)
        article.authors = self._get_authors_for_article(article.pmid)
        article.mesh_terms = self._get_mesh_terms_for_article(article.pmid)
        return article

    def search(
            self,
            keyword: Optional[str] = None,
            year: Optional[int] = None,
            year_from: Optional[int] = None,
            year_to: Optional[int] = None,
            journal: Optional[str] = None,
            author_name: Optional[str] = None,
            mesh_term: Optional[str] = None,
            limit: int = 10,
            offset: int = 0
        )-> list[Article]:

        query = """
        SELECT DISTINCT 
            a.pmid, a.title, a.abstract, a.year, j.name AS journal_name
        FROM articles a
        LEFT JOIN journals j ON a.journal_id = j.id
        LEFT JOIN article_authors aa ON a.pmid = aa.article_pmid
        LEFT JOIN authors au ON aa.author_id = au.id
        LEFT JOIN article_mesh_terms amt ON a.pmid = amt.article_pmid
        LEFT JOIN mesh_terms mt ON amt.mesh_term_id = mt.id
        WHERE 1=1
        """

        params = []

        if keyword:
            query += """
            AND (
                to_tsvector('english', a.title) @@ plainto_tsquery('english', %s)
                OR to_tsvector('english', COALESCE(a.abstract, '')) @@ plainto_tsquery('english', %s)
                )
            """

            params.extend([keyword, keyword])

            if year:
                query += " AND a.publication_year = %s"
                params.append(year)

            if year_from:
                query += " AND a.publication_year >= %s"
                params.append(year_from)

            if year_to:
                query += " AND a.publication_year <= %s"
                params.append(year_to)

            if journal:
                query += " AND j.name ILIKE %s"
                params.append(f"%{journal}%")

            if author_name:
                query += " AND (au.first_name || ' ' || au.last_name) ILIKE %s"
                params.append(f"%{author_name}%")

            if mesh_term:
                query += " AND mt.term ILIKE %s"
                params.append(f"%{mesh_term}%")

        query += " ORDER BY a.publication_year DESC NULLS LAST, a.pmid LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        rows = execute_query(query, tuple(params))

        return [self._row_to_article(row) for row in rows]
    
    def get_all(self, limit: int = 10, offset: int = 0) -> list[Article]:
        return self.search(limit=limit, offset=offset)
    
    def count(self) -> int:
        row = execute_single_query("SELECT COUNT(*) AS count FROM articles")
        return row["count"] if row else 0
    
    def get_years(self) -> list[int]:
        rows = execute_query("SELECT DISTINCT publication_year FROM articles WHERE publication_year IS NOT NULL ORDER BY publication_year DESC")
        return [row["publication_year"] for row in rows]
    
    def get_journals(self) -> list[str]:
        rows = execute_query("SELECT DISTINCT j.name FROM journals j ORDER BY j.name ASC")
        return [row["name"] for row in rows]
    
    def get_top_mesh_terms(self, limit: int = 20) -> list[str]:
        return execute_query(
            """
            SELECT mt.term, COUNT(*) AS term_count
            FROM mesh_terms mt
            JOIN article_mesh_terms amt ON mt.id = amt.mesh_term_id
            GROUP BY mt.term
            ORDER BY term_count DESC
            LIMIT %s
            """,
            (limit,)
        )
    
    def _row_to_article(self, row: dict) -> Article:
        return Article(
            pmid=row["pmid"],
            title=row["title"],
            abstract=row.get("abstract"),
            journal=row.get("journal_name"),
            year=row.get("publication_year"),
            created_at=row.get("created_at")
        )
    
    def _get_authors_for_article(self, pmid: str) -> list[Author]:
        rows = execute_query(
            """
            SELECT au.last_name, au.first_name, au.affiliation
            FROM authors au
            JOIN article_authors aa ON au.id = aa.author_id
            WHERE aa.article_pmid = %s
            ORDER BY aa.author_order ASC
            """,
            (pmid,)
        )

        return [
            Author(
                last_name=row["last_name"],
                first_name=row.get("first_name"),
                affiliation=row.get("affiliation")
            )
            for row in rows
        ]
    
    def _get_mesh_terms_for_article(self, pmid: str) -> list[str]:
        rows = execute_query(
            """
            SELECT mt.term
            FROM mesh_terms mt
            JOIN article_mesh_terms amt ON mt.id = amt.mesh_term_id
            WHERE amt.article_pmid = %s
            ORDER BY mt.term ASC
            """,
            (pmid,)
        )

        return [row["term"] for row in rows]