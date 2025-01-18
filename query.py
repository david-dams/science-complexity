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
        
#     query = """
# SELECT ?item ?itemLabel
# WHERE
# {
#   ?item wdt:P31 wd:Q146. # Must be a cat
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". } # Helps get the label in your language, if not, then default for all languages, then en language
# }
#     """

# # everything thats a formula or a descendent of a formula
# SELECT ?equation ?equationLabel
# WHERE
# {
#   ?equation wdt:P31|wdt:P279* wd:Q976981.     # Instance of or any subclasses of equation 

#   SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
# }    
#     foo = fetch_sparql_results(query)

# # all books by doyle or christie    
# SELECT ?book ?bookLabel
# WHERE
# {
#   VALUES ?value {
#     wd:Q35610
#     wd:Q35064
#   }
  
#   ?book wdt:P50 ?value.
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
# }

# # all of those
# wd:Q246672 # mathematical object
# wd:Q408891 # scientific law
# wd:Q413 # physics

# # which have at least one of these
# wdt:P1249 # time earliest written
# wdt:P577 # pub date
# wdt:P575 # time of discovery

# # all of those
# wd:Q246672 # mathematical object
# wd:Q408891 # scientific law
# wd:Q413 # physics

# # which have at least one of these, where we get the date of bith and date of death of the person
# wdt:P138 # named after
# wdt:P61 # inventor

# # all things invented by or named after tesla ?
# SELECT ?stuff ?stuffLabel
# WHERE
# {
#   VALUES ?value {
#   wdt:P138 # named after
#   wdt:P61 # inventor
#   }
  
#   ?stuff ?value wd:Q9036.
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
# }

# SELECT DISTINCT ?stuff ?stuffLabel
# WHERE
# {
#   VALUES ?v{
#       wdt:P61
#       wdt:P138
#       wdt:P1249 # time earliest written
#       wdt:P577 # pub date
#       wdt:P575 # time of discovery
#       }
    
#   ?stuff (wdt:P31|wdt:P279*) wd:Q976981;
#          ?v ?someguy.
  
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
# }

# # all things with defining equations invented or named after a person and with an attached date
# SELECT DISTINCT ?stuff ?stuffLabel ?equation ?person ?birth
# WHERE
# {
    
#   ?stuff  wdt:P2534 ?equation;
#            (wdt:P138|wdt:P61) ?person.
#              #wdt:P575 ?blanko.
    
#   ?person wdt:P569 ?birth.
  
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
# }

# ORDER BY ?birth
