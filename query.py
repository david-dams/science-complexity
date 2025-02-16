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
from lark import Lark

# Path to your Lark grammar file (adjust this if needed)
grammar_path = "latex.lark"

# Read the grammar file
with open(grammar_path, encoding="utf-8") as f:
    latex_grammar = f.read()

# Initialize Lark parser (mimicking SymPy's approach)
parser = Lark(
    latex_grammar,
    parser="earley",   # Use Earley parser for full LaTeX support
    start="latex_string",
    lexer="auto",
    ambiguity="explicit",
    propagate_positions=False,
    maybe_placeholders=False,
    keep_all_tokens=True
)

# Test parsing
expr = "x = 1"
tree = parser.parse(expr)
print(tree.pretty())
1/0
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
        
    def try_srepr(eqString):
        try:
            return sympy.srepr(sympy.srepr(parse_eq_to_sympy(eqString)))
        except:
            return None

    
    with open(f'{name}.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["eqName", "eqRaw", "eqSympyString", "year", "place"])
        for d in data:
            birthYear = d['birth']            
            eqName = try_get(d, 'stuffLabel')
            eqContent = try_get(dict(html.fromstring(d['equation']).items()), 'alttext')
            eqSympyString = try_srepr(eqContent)
            birthPlace = try_get(d, 'birthPlaceLabel')            
            writer.writerow([eqName, eqContent, eqSympyString, birthYear, birthPlace])
            
# currently, we are getting ~1/3 => 500 invalid vals due to parsing errors (20-ish due to alttext, most of it from sympy, 1 due to missing year)
def try_score(score_func):
    def _inner(exp):
        try:
            return score_func(exp)
        except:
            return np.nan
    return _inner

@try_score
def score_depth(exp):
    def _depth(tup):
        if isinstance(tup, tuple):
            return 1 + max(map(lambda x : depth(x.args), tup), default=0)
        else:
            return 0
    return _depth(exp.args)

@try_score
def score_count(exp):
    return exp.count_ops()
    
def load_df_from_raw(name, score = score_count):
    df = pd.read_csv(f'{name}.csv')
    print(f'{df.isna().sum()} invalid labels, equations')
    df['eq'] = df['eqRaw'].apply(parse_eq_to_sympy)
    print(f'{df.isna().sum()} invalid parsed equations')
    df['year'] = df.year.apply(parse_time_to_centuries)
    print(f'{df.isna().sum()} invalid times')
    df['complexity'] = df['eq'].apply(score)
    print(f'{df.isna().sum()} invalid complexity')
    return df

def parse_eq_to_sympy(eq):
    try:
        eq = eq.replace("{\displaystyle", "")
        return parse_latex(eq)
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

### RICED PLOTTING
def plot_places(df):    
    # Plotting
    df.place.value_counts().head(10).plot(kind='bar', figsize=(10, 6), edgecolor='black')

    # Enhancing the plot
    plt.title('Most Common Birth Places', fontsize=16, weight='bold')  # Title with better styling
    plt.xlabel('Birth Place', fontsize=14)  # Label for the x-axis
    plt.ylabel('Count', fontsize=14)  # Label for the y-axis
    plt.xticks(fontsize=12, rotation=45, ha='right')  # Rotate x-axis labels for better readability
    plt.yticks(fontsize=12)  # Increase y-axis tick label size
    plt.grid(axis='y', linestyle='--', alpha=0.7)  # Add gridlines for clarity

    # Display the plot
    plt.tight_layout()  # Adjust layout to fit all elements nicely
    plt.savefig('birth_places.pdf')

def plot_complexity(df):
    # Plotting
    plt.figure(figsize=(10, 6))  # Set figure size
    plt.plot(df.year, df.complexity, 'o', color='blue', alpha=0.7, label='Complexity')  # Add color and transparency

    # Enhancing the plot
    plt.title('Expression Complexity Over Time', fontsize=16, weight='bold')  # Improve title styling
    plt.xlabel('Year', fontsize=14)  # Label for the x-axis
    plt.ylabel('Complexity', fontsize=14)  # Label for the y-axis
    plt.xticks(fontsize=12)  # Adjust x-axis tick font size
    plt.yticks(fontsize=12)  # Adjust y-axis tick font size
    plt.grid(True, linestyle='--', alpha=0.6)  # Add gridlines for clarity
    plt.legend(fontsize=12, loc='best')  # Add a legend

    # Highlighting trends
    plt.tight_layout()  # Adjust layout to prevent clipping
    plt.savefig('complexity_time.pdf')
    
def plot_years(df):
    # Plotting
    plt.figure(figsize=(10, 6))  # Set figure size
    df.year.hist(bins='auto', edgecolor='black', alpha=0.7, color='skyblue')  # Styling the histogram

    # Enhancing the plot
    plt.title('Year Coverage', fontsize=16, weight='bold')  # Improved title
    plt.xlabel('Year', fontsize=14)  # Label for x-axis
    plt.ylabel('Frequency', fontsize=14)  # Label for y-axis
    plt.xticks(fontsize=12)  # Adjust x-axis tick font size
    plt.yticks(fontsize=12)  # Adjust y-axis tick font size
    plt.grid(axis='y', linestyle='--', alpha=0.6)  # Add gridlines to y-axis for clarity

    # Final adjustments
    plt.tight_layout()  # Ensure all elements fit nicely
    plt.savefig('years_distribution.pdf')

def plot_complexity_hist(df):    
    # Reversing the order of bins
    bins = [-np.inf, 15, 18, np.inf]
    labels = ['Before 15', '15-18', 'After 18']

    # Assigning reversed categories to the DataFrame
    df['time_period'] = pd.cut(df['year'], bins=bins, labels=labels)

    # outliers
    df = df[df['complexity'] < 100]

    # Plotting
    plt.figure(figsize=(10, 6))  # Set figure size
    for period in labels[::-1]:
        df[df['time_period'] == period]['complexity'].hist(
            bins='auto', alpha=0.5, label=period, edgecolor='black'
        )

    # Enhancing the plot
    plt.title('Complexity Distribution for Different Time Periods', fontsize=16, weight='bold')
    plt.xlabel('Complexity', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.legend(fontsize=12, title='Time Period')
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    # Final adjustments
    plt.tight_layout()
    plt.savefig('complexity_hist.pdf')
           
if __name__ == '__main__':
    data_file = 'raw'    
    # download_data(data_file)
    postprocess(data_file)
    df_raw = load_df(data_file)

    plot_places(df_raw)
    
    # discard all invalid vals
    df = df_raw.dropna()
    
    plot_complexity(df)
    plot_years(df)
    plot_complexity_hist(df)
