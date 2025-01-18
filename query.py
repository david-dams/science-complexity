import requests

def fetch_sparql_results(sparql_query):
    """
    Sends a GET request to the Wikidata SPARQL endpoint with the provided query and retrieves the results in JSON format.

    Args:
        sparql_query (str): The SPARQL query string to be sent.

    Returns:
        dict: The JSON response from the server.

    Raises:
        requests.exceptions.RequestException: If the request fails.
    """
    base_url = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
    params = {
        "query": sparql_query,
        "format": "json"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError if the response code is 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    query = """
    SELECT DISTINCT ?stuff ?stuffLabel ?equation ?person ?birth
WHERE
{
    
  ?stuff  wdt:P2534 ?equation;
           (wdt:P138|wdt:P61) ?person.
             #wdt:P575 ?blanko.
    
  ?person wdt:P569 ?birth.
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
}
    """
    res =  fetch_sparql_results(query)
