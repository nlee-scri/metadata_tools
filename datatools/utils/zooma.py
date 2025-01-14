""" For ontology lookups using the Zooma API. """
import requests
import json
from urllib.parse import urlparse
from datatools.utils.utils import apply_to_list
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

@apply_to_list
def parse_ontology_term(url: str) -> Tuple[str, str]:
    """
    Example:
        ontology_name, term_name = parse_ontology_term('http://purl.obolibrary.org/obo/MONDO_0004992')
        print(f"Ontology Name: {ontology_name}, Term Name: {term_name}")
    """

    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split("/")
    ontology_name = path_parts[-2]
    term_name = path_parts[-1]
    return {"Ontology": ontology_name, "Term": term_name}

@dataclass
class zooma:
    def __init__(self, ssl_pem_file_path):
        self.BASE_URL = "https://www.ebi.ac.uk/spot/zooma/v2/api"
        self.ssl_pem_file_path = ssl_pem_file_path

    def is_valid_url(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def join_url(self, *args):
        return "/".join(map(lambda x: str(x).strip("/"), args))

    def handle_request(self, method, endpoint, params=None):
        url = self.join_url(self.BASE_URL, endpoint)
        try:
            if method == "GET":
                response = requests.get(
                    url, params=params, verify=self.ssl_pem_file_path
                )
            elif method == "POST":
                response = requests.post(
                    url, json=params, verify=self.ssl_pem_file_path
                )
            else:
                raise ValueError("Unsupported HTTP method")

            response.raise_for_status()
            return response
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return response

    def general_get(self, endpoint, params):
        response = self.handle_request("GET", endpoint, params)
        return response
    
    def response_to_df(self, response):
        
        data = json.loads(response.text)
        print("Number of results: ", len(data))
        print("Results: ")
        combined_dict = [
            {
                **d["annotatedProperty"],
                **parse_ontology_term(d["semanticTags"])[0],
                "Confidence": d["confidence"],
            }
            for d in data
        ]
        results = pd.DataFrame(combined_dict).sort_values(
            "Confidence", ascending=True
        )
        
        results.dropna(how='all', inplace=True, axis=1)
        print(results)
        
        return results


    def get_annotations(self, term):
        # predicting annotations

        endpoint = "/services/annotate"

        print("Term: ", term)
        term = term.replace(" ", "+").lower()

        params = {"propertyValue": term}

        response = self.handle_request("GET", endpoint, params)


        if response.status_code == 200:
            data = json.loads(response.text)
            results = self.response_to_df(response)

            return data, results
        else:

            return None