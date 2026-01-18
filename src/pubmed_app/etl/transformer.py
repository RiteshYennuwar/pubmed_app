from pubmed_app.config.logger import logger
from dataclasses import dataclass, field
from typing import Optional
import re
import html

@dataclass
class Author:
    last_name: str
    fore_name: Optional[str] = None
    initials: Optional[str] = None

@dataclass
class Article:
    pmid: str
    title: str
    abstract: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    authors: list[Author] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)

class ArticleTransformer:
    def transform(self, parsed_articles: list[dict]) -> list[Article]:
        articles = []
        skipped = 0

        for data in parsed_articles:
            article = self._transform_article(data)
            if article:
                articles.append(article)
            else:
                skipped += 1

        logger.info(f"Transformed {len(articles)} articles, skipped {skipped} articles due to missing essential fields.")
        return articles
    
    def _transform_article(self, data: dict) -> Optional[Article]:
        pmid = data.get("pmid","").strip()
        title = self._clean_text(data.get("title",""))

        if not pmid or not title:
            logger.warning(f"Skipping article due to missing PMID or title. Data: {data}")
            return None
        
        return Article(
            pmid=pmid,
            title=title,
            abstract=self._clean_text(data.get("abstract")),
            journal=self._clean_text(data.get("journal",{}).get("name")),
            year=self._validate_year(data.get("year")),
            authors=self._transform_authors(data.get("authors", [])),
            mesh_terms=self._clean_mesh_terms(data.get("mesh_terms", [])),
            )
    
    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        
        text = html.unescape(text)

        text = re.sub(r'<[^>]+>', '', text)

        text = re.sub(r'\s+', ' ', text).strip()

        return text if text else None
    
    def _validate_year(self, year: Optional[int]) -> Optional[int]:
        if year is None:
            return None
        
        if 1800 <= year <= 2100:
            return year
        
        logger.warning(f"Invalid year '{year}' encountered. Setting year to None.")
        return None
    
    def _transform_authors(self, authors_data: list[dict]) -> list[Author]:
        authors = []
        for author_data in authors_data:
            last_name = author_data.get("last_name")
            if not last_name:
                continue
            
            author = Author(
                last_name=last_name,
                fore_name=author_data.get("fore_name",""),
                initials=author_data.get("initials","")
            )
            authors.append(author)
        return authors
    
    def _clean_mesh_terms(self, mesh_terms: list[str]) -> list[str]:
        cleaned_terms = []
        seen = set()

        for term in mesh_terms:
            term = self._clean_text(term)
            if term and term not in seen:
                cleaned_terms.append(term)
                seen.add(term.lower())

        return cleaned_terms