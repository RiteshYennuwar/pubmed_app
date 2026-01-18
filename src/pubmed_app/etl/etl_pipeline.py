from pubmed_app.config.logger import logger
from pubmed_app.etl.pubmend_client import PubMedClient

class ETLPipeline:
    def __init__(self, email: str, api_key: str = None):
        self.client = PubMedClient(email=email, api_key=api_key)

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

        logger.info("ETL pipeline completed successfully")



if __name__ == "__main__":
    from pubmed_app.config.settings import settings

    etl_pipeline = ETLPipeline(
        email=settings.PUBMED_EMAIL,
        api_key=settings.PUBMED_API_KEY
    )
    etl_pipeline.run(search_term="cancer", retmax=10)