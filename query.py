import requests
import json
import pickle
import datetime
import csv

from lxml import html
from sympy.parsing.latex import parse_latex

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# TODO: complexity
# TODO: hist birth place
# TODO: replace sympy 

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
# currently, we are losing ~1/3 => 500 eqs due to parsing errors (20-ish due to alttext, most of it from sympy)
def get_eqs_to_dates_dict(name):    
    
    parse_eq = lambda txt : parse_latex(txt.replace("{\displaystyle", ""))

    raw = load(name)    
    data = raw['results']['bindings']
    res, errs_alt, errs_eq = {}, {}, {}
    
    for d in data:
        eq_html = html.fromstring(d['equation']['value'])
        try:
            eq_txt = dict(eq_html.items())['alttext']
        except Exception as e:
            errs_alt[eq_txt] = d
        date = d['birth']['value']
        
        try:
            eq = parse_eq(eq_txt)
            res[eq] = date
        except Exception as e:
            errs_eq[eq_txt] = e
            
    return res, errs_alt, errs_eq

def postprocess(name, print_errs = False):
    """turns raw data into csv file with structure

    equation_raw_string, date_raw_string, birthplace_raw_string
    """
    
    parse_eq = lambda txt : parse_latex(txt.replace("{\displaystyle", ""))

    data = load(name)

    def try_get(d, key):
        try:
            return d[key]
        except:
            return None        
    
    with open('output.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        for d in data:
            birthYear = d['birth']
            eqName = try_get(d, 'stuffLabel')            
            eqContent = try_get(dict(html.fromstring(d['equation']).items()), 'alttext')                           
            birthPlace = try_get(d, 'birthPlaceLabel')
            writer.writerow([eqName, eqContent, birthYear, birthPlace])


def parse_time_to_centuries(s):
    """parses string to time measured in units of 100yrs"""
    # pattern '-1702-01-01T00:00:00Z'
    parse = lambda x : datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')
    # offset by 1y1m1d
    fixed_date = parse('0001-01-01T00:00:00Z')
    
    if s.startswith('-'):
        ret = fixed_date - parse(s[1:])
    else:
        ret = parse(s) - fixed_date
        
    # undo offset
    return (ret.days - 365 - 31 - 1) / (365 * 100)

def max_date(res):
    vals = res.values()    
    m = datetime.datetime.min
    for s in vals:
        parse = lambda x : datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')
        if not s.startswith('-'):
            l = parse(s)
            m = l if l > m else m
    return m

def summarize(res):
    print(f'eqns: {len(res)}. max_date : {max_date(res)}.')    

def histogram(res):
    """displays histogram of equation invention years (proxied by date of birth of inventor / naming person)"""
    vals = res.values()    
    m = [parse_time_to_centuries(s) for s in vals]
    plt.hist(m, bins = 'auto')
    plt.savefig("eqns_years.pdf")
    plt.close()
    
def get_time_complexity(res):
    return np.array([(parse_time_to_centuries(year), exp.count_ops()) for exp, year in res.items()]).T

def filter_time_complexity(comp, c_lower = -np.inf, c_upper = np.inf, y_lower = -np.inf, y_upper = np.inf):
    idxs = (c_lower < comp[1]) & (comp[1] < c_upper) & (y_lower < comp[0]) & (comp[0] < y_upper)
    return comp[:, idxs]

def time_complexity(res):
    comp = get_time_complexity(res)
    plt.plot(comp[0], comp[1], 'o')
    plt.show()
    plt.close()
    
def hist_complexity(res):
    density = True

    def add_hist(label, c_lower = -np.inf, c_upper = np.inf, y_lower = -np.inf, y_upper = np.inf):
        comp_filtered = filter_time_complexity(comp, c_lower, c_upper, y_lower, y_upper)
        plt.hist(comp_filtered[1], bins = 'auto', density = True, label = label, alpha = 0.8)
        
    
    comp = get_time_complexity(res)
    
    c_limit = np.inf
    add_hist('<15', y_upper = 15, c_upper = c_limit)
    add_hist('15-18', y_lower = 14, y_upper = 19, c_upper = c_limit)
    add_hist('>18', y_lower = 18, c_upper = c_limit)

    plt.legend()
    plt.show()
    plt.close()

if __name__ == '__main__':
    data_file = 'raw'
    
    # download_data(data_file)
    postprocess(data_file)
    
    # import pdb; pdb.set_trace()

    # sympy latex parsing takes long
    # res, _, _ = get_eqs_to_dates_dict(data_file)
    
    # summarize(res)

    # histogram(res)

    hist_complexity(res)    
