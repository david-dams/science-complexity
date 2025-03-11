import requests
import json
import pickle
import datetime
import csv

from lxml import html, etree
import sympy
from sympy.parsing.latex import parse_latex

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import subprocess

### FILE HANDLING
def save(res, name = 'data'):
    with open(f'{name}.json', 'w') as fp:
        json.dump(res, fp)
        
def load(name):
    with open(f"{name}.json", 'r') as fp:
        return json.load(fp)
    
### POSTPROCESSING
def extract_data(name):
    """returns a list of readable dicts containing equation string, year, name, country
    """

    entries = load(name)
    ret = []
    
    dropout = 0
    for entry in entries:                
        try:
            equation = dict(
                html.fromstring(entry['equation']).items()
            )
            # 13 eqs dont have alttext bc of some internal parsing error
            content = equation['alttext']

            # country is not that important
            country = entry['birthPlaceLabel'] if 'birtPlaceLabel' in entry else None

            # these are okay
            year = entry['birth']
            name = entry['stuffLabel']
            
            ret.append( {"content" : content, "year" : year, "name" : name, "country" : country} )
            
        except:
            dropout += 1
            
    print(f"Dropout: {dropout}")

    return ret

def data_to_tex(data):
    """writes all equations into a minimal tex file to be processed by latexml"""
    
    header = r"\documentclass{article} \usepackage[margin=0.7in]{geometry} \usepackage[parfill]{parskip} \usepackage[utf8]{inputenc}\usepackage{amsmath,amssymb,amsfonts,amsthm} \begin{document}"
    footer = r"\end{document}"
    
    eq_env = r"\begin{equation} INSERT \end{equation}"    
    eq_block = "\n"
    for element in data:
        eq_block += eq_env.replace("INSERT", element["content"]) + "\n"

    content = header + eq_block + footer
    
    with open("data.tex", "w") as f:
        f.write(content)


def tex_to_xml():
    """runs latexml"""

    # Define the command and arguments
    command = ["latexml", "--dest=data.xml", "data.tex"]

    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)

    # Print the output
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

def xml_to_pandas():
    tree = etree.parse("data.xml")
    equations = [y for y in [x for x in tree.getroot()][2]]
    
    import pdb; pdb.set_trace()
                          
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
    # equations = extract_data(DATA_FILE)
    # data_to_tex(equations)
    # tex_to_xml()
    xml_to_pandas()
