from typing import Optional

from pubmed_app.config.logger import logger
from pubmed_app.database.curd import ArticleCRUD, Article

class SearchService:
    def __init__(self):
        self.article_crud = ArticleCRUD()

    def search_articles(
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
        ) -> list[Article]:

        logger.info(f"Searching articles with keyword={keyword}, year={year}, year_from={year_from}, year_to={year_to}, journal={journal}, author_name={author_name}, mesh_term={mesh_term}, limit={limit}, offset={offset}")

        articles = self.article_crud.search(
            keyword=keyword,
            year=year,
            year_from=year_from,
            year_to=year_to,
            journal=journal,
            author_name=author_name,
            mesh_term=mesh_term,
            limit=limit,
            offset=offset
        )

        logger.info(f"Found {len(articles)} articles matching the search criteria")

        return articles
    
    def get_filter_options(self) -> dict:
        return {
            "years": self.article_crud.get_years(),
            "journals": self.article_crud.get_journals(),
            "mesh_terms": [item["term"] for item in self.article_crud.get_top_mesh_terms(30)]
        }
    
    def get_stats(self) -> dict:
        years = self.article_crud.get_years()
        return {
            "total_articles": self.article_crud.count(),
            "year_range": f"{years[-1]} - {years[0]}" if years else "N/A",
            "total_journals": len(self.article_crud.get_journals()),
        }