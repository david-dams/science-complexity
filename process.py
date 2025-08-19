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

import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss

from pprint import pprint

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
            country = entry['birthPlaceLabel'] if 'birthPlaceLabel' in entry else None
            
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
    
    eq_env = r"\begin{equation} INSERT LABEL\end{equation}"    
    eq_block = "\n"
    for element in data:
        year, country, name = element["year"], element["country"], element["name"]
        label = "\\label{" + f"year={year}" + f", country={country}, " + f"name={name}" + "}"        
        eq_block += eq_env.replace("INSERT", element["content"]).replace("LABEL", label) + "\n"

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
    
def compute_depth(elem, current=0):
    """Compute max depth of XML tree."""
    
    # only increment for legal
    children = list(elem)
    if not children:
        return current
    
    return max(compute_depth(child, current + 1) for child in children)

def is_token(elem):
    return 'role' in elem.keys()

def print_elem(elem):
    print(len(list(elem)))
    for x in list(elem):
        print(" ", x.text, " ")
        
def print_tree(elem, current = 0, show_level = False):
    
    if is_token(elem):
        level = f"level: {current}" if show_level else ""
        print(" " * current, elem.text or dict(elem.items())["role"], level)

    children = list(elem)
    for child in children:
        print_tree(child, current + 1)        
        
def compute_nodes(elem, current=0):
    """Compute number of nodes in XML tree."""
    children = list(elem)
    if not children:
        return current + is_token(elem)
    return sum(compute_nodes(child, current + is_token(elem)) for child in children)

def process_equation(eq, label):
    # Define namespace mapping
    ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}

    # labels always look like year, country, name
    labels = label.replace("LABEL:", "").split(",")        
    year = parse_time_to_centuries(labels[0].split("=")[-1])
    country = labels[1].split("=")[-1]
    name = labels[2].split("=")[-1]        
    xmath = eq.find('.//ltx:XMath', namespaces=ns)
    
    return {"year" : year,
            "name" : name,
            "country" : country,
            "raw" : xmath}
    
def xml_to_pandas(data):    
    tree = etree.parse("data.xml")
    root = tree.getroot()
    
    # Define namespace mapping
    ns = {'ltx': 'http://dlmf.nist.gov/LaTeXML'}

    # Find all single equations
    single_equations = root.xpath('//ltx:equation[not(ancestor::ltx:equationgroup)]', namespaces=ns)
    dict_list = [process_equation(eq, eq.get('labels')) for eq in single_equations]
    
    # Find all equation groups
    equation_groups = root.findall('.//ltx:equationgroup', namespaces=ns)

    group_data = []
    for group in equation_groups:
        labels = group.get('labels')
        dict_list += [process_equation(eq, labels) for eq in group.findall(".//ltx:equation", namespaces=ns)]
        
    df = pd.DataFrame(dict_list)
    
    return df
            
                          
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
    df.country.value_counts().head(10).plot(kind='bar', figsize=(10, 6), edgecolor='black')

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

def plot_hist(df, key, bins = None, labels = None, label = None):    
    # Reversing the order of bins
    bins = bins or [-np.inf, 15, 18, np.inf]
    labels = labels or ['Before 15', '15-18', 'After 18']

    # Assigning reversed categories to the DataFrame
    df['time_period'] = pd.cut(df['year'], bins=bins, labels=labels)

    # outliers
    df = df[df[key] < 100]

    # Plotting
    plt.figure(figsize=(10, 6))  # Set figure size
    for period in labels[::-1]:
        df[df['time_period'] == period][key].hist(
            bins='auto', alpha=0.5, label=period, edgecolor='black'
        )

    # Enhancing the plot
    label = label or 'Complexity'
    plt.title(f'{label} Distribution for Different Time Periods', fontsize=16, weight='bold')
    plt.xlabel(f"{label}", fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.legend(fontsize=12, title='Time Period')
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    # Final adjustments
    plt.tight_layout()
    plt.savefig(f'{key}_hist.pdf')
    
def plot_complexity(df, key, year = -np.inf, label = None):
    # Plotting
    plt.figure(figsize=(10, 6))  # Set figure size
    # plt.plot(df.year, df.complexity, 'o', color='blue', alpha=0.7, label='Complexity')  # Add color and transparency
    
    # Group by year and calculate mean & standard deviation
    summary = df.groupby('year')[key].agg(['mean', 'std']).reset_index()

    # Plot
    label = label or 'Complexity'
    plt.figure(figsize=(8, 5))
    idxs = summary["year"] >= year
    plt.errorbar(summary['year'][idxs], summary['mean'][idxs], yerr=summary['std'][idxs],
                 fmt='o-', color='blue', ecolor='gray', capsize=5, alpha=0.8,
                 label=f'Mean {label} ± SD')
    
    # Enhancing the plot
    plt.title(f'Expression {label} Over Time', fontsize=16, weight='bold')  # Improve title styling
    plt.xlabel('Year', fontsize=14)  # Label for the x-axis
    plt.ylabel(label, fontsize=14)  # Label for the y-axis
    plt.xticks(fontsize=12)  # Adjust x-axis tick font size
    plt.yticks(fontsize=12)  # Adjust y-axis tick font size
    plt.grid(True, linestyle='--', alpha=0.6)  # Add gridlines for clarity
    plt.legend(fontsize=12, loc='best')  # Add a legend

    # Highlighting trends
    plt.tight_layout()  # Adjust layout to prevent clipping
    plt.savefig(f'{key}_time.pdf')
    
def get_statistics(df, key, upper = np.inf, lower = -np.inf):
    X = df[key]
    legal = ~np.logical_or(df.year.isna(), df[key].isna())
    legal = np.logical_and(legal, np.logical_and(df.year <= upper, df.year >= lower))
    years = np.array(df.year[legal])
    complexity = np.array(df[key][legal])

    # OLS regression
    X_with_const = sm.add_constant(years)
    model = sm.OLS(complexity, X_with_const).fit()

    adf_result = adfuller(complexity)
    kpss_result = kpss(complexity, regression='c', nlags='auto')
    complexity_diff = np.diff(complexity)
    kpss_diff_result = kpss(complexity_diff, regression='c', nlags='auto')

    return {
        "OLS": {
            "slope": model.params[1],
            "p_value": model.pvalues[1],
        },
        "ADF": {
            "statistic": adf_result[0],
            "p_value": adf_result[1],
            "critical_values": adf_result[4],
        },
        "KPSS": {
            "statistic": kpss_result[0],
            "p_value": kpss_result[1],
            "critical_values": kpss_result[3],
        },
        "KPSS_diff": {
            "statistic": kpss_diff_result[0],
            "p_value": kpss_diff_result[1],
            "critical_values": kpss_diff_result[3],
        },
    }

def get_df_from_raw_data():
    raparse()
    return get_gf()
    
def reparse():
    data_to_tex("raw.json")
    tex_to_xml()

def get_df():
    DATA_FILE = 'raw'
    equations = extract_data(DATA_FILE)
    df = xml_to_pandas(equations)
    return df

def debug_info():
    eq = df.iloc[0].raw
    print_tree(eq); print(compute_nodes(eq)); print(compute_depth(eq))
    eq = df.iloc[-1].raw
    print_tree(eq); print(compute_nodes(eq)); print(compute_depth(eq))

def attach_column(df, func, label):
    col = len(df.columns)
    df.insert(col, label, [func(x) if x is not None else None for x in df.raw ])
    
if __name__ == '__main__':
    df = get_df()

    attach_column(df, compute_depth, "depth")
    attach_column(df, compute_nodes, "nodes")
        
    # plot_places(df)
    # plot_years(df)

    lower, upper = 18, np.inf
    plot_complexity(df, year = lower, key = "depth", label = "Tree Depth")
    plot_hist(df, key = "depth", label = "Tree Depth")
    pprint(get_statistics(df, "depth", lower = lower, upper = np.inf))

    plot_complexity(df, year = 18, key = "nodes", label = "Node Count")
    plot_hist(df, key = "nodes", label = "Node Count")
    pprint(get_statistics(df, "nodes", lower = lower, upper = np.inf))
