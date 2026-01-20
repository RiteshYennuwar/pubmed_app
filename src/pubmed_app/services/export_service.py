import csv
import json
from pathlib import Path
from typing import Union
from io import StringIO, BytesIO

from pubmed_app.config import logger
from pubmed_app.database import Article


class ExportService:
    
    def to_csv(self, articles: list[Article], filepath: Union[str, Path, None] = None) -> Union[Path, str]:

        logger.info(f"Exporting {len(articles)} articles to CSV")
        
        rows = []
        for article in articles:
            rows.append({
                "pmid": article.pmid,
                "title": article.title,
                "abstract": article.abstract or "",
                "journal": article.journal_name or "",
                "year": article.publication_year or "",
                "authors": article.authors_str if article.authors else "",
                "mesh_terms": "; ".join(article.mesh_terms) if article.mesh_terms else "",
            })
        
        fieldnames = ["pmid", "title", "abstract", "journal", "year", "authors", "mesh_terms"]
        
        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"CSV export complete: {filepath}")
            return filepath
        else:
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            return output.getvalue()
    
    def to_json(self, articles: list[Article], filepath: Union[str, Path, None] = None) -> Union[Path, str]:
        logger.info(f"Exporting {len(articles)} articles to JSON")
        
        data = []
        for article in articles:
            data.append({
                "pmid": article.pmid,
                "title": article.title,
                "abstract": article.abstract,
                "journal": article.journal_name,
                "year": article.publication_year,
                "authors": [
                    {
                        "last_name": a.last_name,
                        "first_name": a.first_name,
                        "affiliation": a.affiliation,
                    }
                    for a in article.authors
                ] if article.authors else [],
                "mesh_terms": article.mesh_terms or [],
            })
        
        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON export complete: {filepath}")
            return filepath
        else:
            return json.dumps(data, indent=2, ensure_ascii=False)
