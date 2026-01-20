from pubmed_app.config.logger import logger
from pubmed_app.etl.pubmend_client import PubMedClient
from pubmed_app.etl.parser import PubMedParser
from pubmed_app.etl.transformer import ArticleTransformer
from pubmed_app.etl.loader import DatabaseLoader

class ETLPipeline:
    def __init__(self, email: str, api_key: str = None):
        self.client = PubMedClient(email=email, api_key=api_key)
        self.parser = PubMedParser()
        self.transformer = ArticleTransformer()
        self.loader = DatabaseLoader()

    def run(self, search_term: str, retmax: int = 20):
        logger.info(f"Starting ETL pipeline for search term: {search_term}")
        
        logger.info("Extracting data from PubMed")
        search_results = self.client.search(term=search_term, retmax=retmax)
        id_list = search_results.get("esearchresult", {}).get("idlist", [])
        logger.info(f"Search results: {search_results}") # todo: remove this line later
        logger.info(f"Found {len(id_list)} articles")

        if not id_list:
            logger.warning("No articles found, ending pipeline.")
            return

        logger.info("Transforming data")
        fetched_data = self.client.fetch(id_list=id_list)

        logger.info(f"fetched_data {fetched_data[:500]}...") # todo: remove this line later
        logger.info(f"Fetched data length: {len(fetched_data)} characters")

        parsed_articles = self.parser.parse(fetched_data)
        transformed_articles = self.transformer.transform(parsed_articles)

        logger.info(f"transformed_articles {transformed_articles[:2]}...") # todo: remove this line later   
        logger.info(f"Transformed {len(transformed_articles)} articles")

        if not transformed_articles:
            logger.warning("No articles to load, ending pipeline.")
            return {"error": "No articles to load"}

        logger.info("Loading data to destination")
        stats = self.loader.load(transformed_articles)
        logger.info(f"Load stats: {stats}")

        logger.info("ETL pipeline completed successfully")
        return stats



if __name__ == "__main__":
    from pubmed_app.config.settings import settings

    etl_pipeline = ETLPipeline(
        email=settings.PUBMED_EMAIL,
        api_key=settings.PUBMED_API_KEY
    )
    etl_pipeline.run(search_term="cancer", retmax=10)