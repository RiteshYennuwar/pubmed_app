import requests
import time
from typing import Optional

class PubMedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    def __init__(self, email: str, api_key: Optional[str] = None):
        self.email = email
        self.api_key = api_key

    def _get_params(self, additional_params: dict) -> dict:
        params = {"email": self.email}
        if self.api_key:
            params["api_key"] = self.api_key
        params.update(additional_params)
        return params

    def search(self, term: str, retmax: int = 20) -> dict:
        url = f"{self.BASE_URL}esearch.fcgi"
        params = self._get_params({
            "db": "pubmed",
            "term": term,
            "retmax": retmax,
            "retmode": "json"
        })
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def fetch(self, id_list: list) -> dict:
        url = f"{self.BASE_URL}efetch.fcgi"
        ids = ",".join(id_list)
        params = self._get_params({
            "db": "pubmed",
            "id": ids,
            "retmode": "xml"
        })
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.text