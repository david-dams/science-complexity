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

### FILE HANDLING
def save(res, name = 'data'):
    with open(f'{name}.json', 'w') as fp:
        json.dump(res, fp)
        
def load(name):
    with open(f"{name}.json", 'r') as fp:
        return json.load(fp)
    
### POSTPROCESSING
def run_latexml(name):
    """creates a moc tex doc from raw.json and runs latexml
    """
    
    return


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
    DATA_FILE = 'raw'
    run_latexml(DATA_FILE)
