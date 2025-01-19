import requests
import json
import pickle
import datetime
import csv

from lxml import html
import sympy
from sympy.parsing.latex import parse_latex

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# TODO: replace sympy 
# TODO: alternative complexity measures?

### FILE HANDLING
def save(res, name = 'data'):
    with open(f'{name}.json', 'w') as fp:
        json.dump(res, fp)
        
def load(name):
    with open(f"{name}.json", 'r') as fp:
        return json.load(fp)

### WEB
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
        
def download_data(name):
    query = """
SELECT DISTINCT ?stuff ?stuffLabel ?equation ?person ?birth ?birthPlace ?birthPlaceLabel
WHERE
{
    
  ?stuff  wdt:P2534 ?equation;
           (wdt:P138|wdt:P61) ?person.
    
  ?person wdt:P569 ?birth.
  
  OPTIONAL {?person wdt:P19 ?tmp.
            ?tmp wdt:P17 ?birthPlace.}
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
}
    """
    res =  fetch_sparql_results(query)
    save(res, name)
    
### POSTPROCESSING
def postprocess(name):
    """saves raw data into csv file containing raw strings for

    equation name, equation, date, birthplace
    """
     
    data = load(name)

    def try_get(d, key):
        try:
            return d[key]
        except:
            return None        
    
    with open(f'{name}.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["eqName", "eq", "year", "place"])
        for d in data:
            birthYear = d['birth']
            eqName = try_get(d, 'stuffLabel')            
            eqContent = try_get(dict(html.fromstring(d['equation']).items()), 'alttext')                           
            birthPlace = try_get(d, 'birthPlaceLabel')
            writer.writerow([eqName, eqContent, birthYear, birthPlace])
            
# currently, we are getting ~1/3 => 500 invalid vals due to parsing errors (20-ish due to alttext, most of it from sympy, 1 due to missing year)
def load_df(name):
    df = pd.read_csv(f'{name}.csv')
    print(f'{df.isna().sum()} invalid labels, equations')
    df['eq'] = df['eq'].apply(parse_eq_to_sympy)
    print(f'{df.isna().sum()} invalid parsed equations')
    df['year'] = df.year.apply(parse_time_to_centuries)
    print(f'{df.isna().sum()} invalid times')
    df['complexity'] = df['eq'].apply(score_complexity)
    print(f'{df.isna().sum()} invalid complexity')
    return df

def score_complexity(x):
    try:
        return x.count_ops()
    except:
        return np.nan

def parse_eq_to_sympy(eq):
    try:
        return parse_latex(eq.replace("{\displaystyle", ""))
    except Exception as e:
        return None    
            
def parse_time_to_centuries(s):
    """parses string to time measured in units of 100yrs"""
    # pattern '-1702-01-01T00:00:00Z'
    parse = lambda x : datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')
    # offset by 1y1m1d
    fixed_date = parse('0001-01-01T00:00:00Z')

    try:
        if s.startswith('-'):
            ret = fixed_date - parse(s[1:])
        else:
            ret = parse(s) - fixed_date
    except ValueError:
        return None
        
    # undo offset
    return (ret.days - 365 - 31 - 1) / (365 * 100)

if __name__ == '__main__':
    data_file = 'raw'    
    # download_data(data_file)
    # postprocess(data_file)
    df_raw = load_df(data_file)
    
    df_raw.place.value_counts().head(10).plot(kind='bar')    
    plt.title('most common birth places')
    plt.show()
    
    # discard all invalid vals
    df = df_raw.dropna()
    
    plt.plot(df.year, df.complexity, 'o')
    plt.title('expression complexity over time')
    plt.show()
    
    df.year.hist(bins = 'auto')
    plt.title('year coverage')
    plt.show()
    
    df.groupby( pd.cut(df['year'], [-np.inf, 15, 18, np.inf] ))['complexity'].hist(bins = 'auto', alpha = 0.3, legend = True)
    plt.title('complexity distribution for different time periods')
    plt.show()    
