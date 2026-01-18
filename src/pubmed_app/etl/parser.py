from pubmed_app.config.logger import logger
import xml.etree.ElementTree as ET
from typing import Optional

class PubMedParser:
    def parse(self, xml_string: str) -> list[dict]:
        
        if not xml_string.strip():
            logger.warning("Empty XML string provided to parser.")
            return []
        
        articles = []

        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
            return []
        
        for article_element in root.findall(".//PubmedArticle"):
            try:
                article = self._parse_article(article_element)
                if article:
                    articles.append(article)
            except Exception as e:
                pmid = self._get_text(article_element, ".//PMID", "Unknown")
                logger.error(f"Error parsing article element with PMID {pmid}: {e}")
                continue

        logger.info(f"Parsed {len(articles)} articles from XML.")
        return articles
    
    def _parse_article(self, element: ET.Element) -> Optional[dict]:
        citation = element.find("MedlineCitation")
        if citation is None:
            return None
        artical = citation.find("Article")
        if artical is None:
            return None
        
        return {
            "pmid": self._get_text(citation, "PMID"),
            "title": self._get_text(artical, "ArticleTitle"),
            "abstract": self._get_abstract(artical),
            "journal": self._get_journal(artical),
            "year": self._get_year(artical),
            "authors": self._get_authors(artical),
            "mesh_terms": self._get_mesh_terms(citation)
        }
    
    def _get_text(self, element: ET.Element, path: str, default: str = "") -> str:
        found = element.find(path)
        if found is not None and found.text:
            return found.text.strip()
        return default
    
    def _get_abstract(self, article: ET.Element) -> Optional[str]:
        abstract_element = article.find("Abstract")
        if abstract_element is None:
            return None
        
        texts = []
        for text_element in abstract_element.findall("AbstractText"):
            label = text_element.get("Label", "")
            text = text_element.text or ""

            if label:
                texts.append(f"{label}: {text.strip()}")
            else:
                texts.append(text.strip())

        return " ".join(texts) if texts else None
    
    def _get_journal(self, article: ET.Element) -> str:
        journal_element = article.find("Journal")
        if journal_element is None:
            return {"name": ""," issn": ""}
        
        return {
            "name": self._get_text(journal_element, "Title"),
            "issn": self._get_text(journal_element, "ISSN")
        }
    
    def _get_year(self, article: ET.Element) -> Optional[int]:
        paths = [
            "Journal/JournalIssue/PubDate/Year",
            "ArticleDate/Year"
        ]

        for path in paths:
            year_text = self._get_text(article, path)
            if year_text and year_text.isdigit():
                return int(year_text)
            
        medline_date = self._get_text(article, "Journal/JournalIssue/PubDate/MedlineDate")
        if medline_date:
            year_part = medline_date.split(" ")[0]
            if year_part.isdigit():
                return int(year_part)
        return None
    
    def _get_authors(self, article: ET.Element) -> list[dict]:
        authors = []
        author_list = article.find("AuthorList")
        if author_list is None:
            return authors
        
        for author_element in author_list.findall("Author"):
            author = {
                "last_name": self._get_text(author_element, "LastName"),
                "first_name": self._get_text(author_element, "ForeName"),
                "affiliation": self._get_text(author_element, "AffiliationInfo/Affiliation")
            }

            if author["last_name"]:
                authors.append(author)

        return authors
    
    def _get_mesh_terms(self, citation: ET.Element) -> list[str]:
        mesh_terms = []
        mesh_heading_list = citation.find("MeshHeadingList")
        if mesh_heading_list is None:
            return mesh_terms
        
        for mesh_heading in mesh_heading_list.findall("MeshHeading"):
            descriptor = self._get_text(mesh_heading, "DescriptorName")
            if descriptor:
                mesh_terms.append(descriptor)

        return mesh_terms