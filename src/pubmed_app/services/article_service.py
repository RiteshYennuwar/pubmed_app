from typing import Optional

from pubmed_app.config.logger import logger
from pubmed_app.database.curd import ArticleCRUD, Article

class ArticleService:
    def __init__(self):
        self.article_crud = ArticleCRUD()

    def get_article_by_pmid(self, pmid: str) -> Optional[Article]:
        logger.info(f"Fetching article with PMID: {pmid}")
        article = self.article_crud.get_by_pmid(pmid)
        if article:
            logger.info(f"Article found: {article.title}")
        else:
            logger.warning(f"No article found with PMID: {pmid}")
        return article
    
    def get_article_by_id(self, article_id: int) -> Optional[Article]:
        logger.info(f"Fetching article with ID: {article_id}")
        article = self.article_crud.get_by_id(article_id)
        if article:
            logger.info(f"Article found: {article.title}")
        else:
            logger.warning(f"No article found with ID: {article_id}")
        return article
    
    def get_recent_articles(self, limit: int = 10) -> list[Article]:
        logger.info(f"Fetching {limit} most recent articles")
        articles = self.article_crud.get_all(limit)
        logger.info(f"Fetched {len(articles)} articles")
        return articles
    
    def get_pubmed_url(self, pmid: str) -> str:
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        logger.info(f"Generated PubMed URL for PMID {pmid}: {url}")
        return url