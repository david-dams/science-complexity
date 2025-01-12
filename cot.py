import re
import os
import json

import requests
from lxml import html
from sympy.parsing.latex import parse_latex
from sympy.parsing.latex.errors import LaTeXParsingError

def filename(url: str) -> str:
    return f"content/{url.split('/')[-1]}.html"

def save_page(url: str) -> None:
    """
    Downloads the Wikipedia page from the provided URL and saves its HTML content to a file.
    
    :param url: The URL of the Wikipedia page.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
            
        # Save the HTML content to a file (UTF-8 encoding for safety)
        with open(filename(url), "w", encoding="utf-8") as f:
            f.write(response.text)
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the page: {e}")

def extract_equations(filename: str) -> list:
    """
    Extracts all equations from <math> tags within the saved HTML file.
    Wikipedia often stores mathematical expressions in <math> tags.
    
    :param filename: The path to the file containing the HTML content.
    :return: A list of mathematical expressions found in <math> tags.
    """
    try:
        # Read the file content
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
            
        tree = html.fromstring(content)        
        annotations = tree.findall(".//annotation")
        equations = [parse(a.text.replace("{\displaystyle", "")) for a in annotations]
                
    except Exception as e:
        print(f"An error occurred while extracting equations: {e}")

    return equations

def parse(latex_eq):    
    try:
        parsed_eq = parse_latex(latex_eq)
    except:
        # print(f"Error on {latex_eq}")
        return None
    
    return parsed_eq

def score(eqns : list) -> float:
    """
    scores complexity of equation list
    """
    
    filtered = [x for x in eqns if x is not None]
    try:
        return sum(map(lambda x : x.count_ops(), filtered)) / len(filtered)
    except:
        return None

def extract_urls(filename: str) -> list:
    """
    Extracts all hyperlinks (URLs) from the saved HTML file.
    
    :param filename: The path to the file containing the HTML content.
    :return: A list of extracted URL strings.
    """
    urls = []
    try:
        # Read the file content
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()

        # Parse with lxml.html
        tree = html.fromstring(content)

        # Extract all href attributes from <a> tags
        urls = ["https://en.wikipedia.org" + x for x in tree.xpath('//a/@href') if "wiki" in x]
        
        print(f"Found {len(urls)} URLs in {filename}")
        
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"An error occurred while extracting URLs: {e}")
    
    return urls

def download_list_page(url):
    """downloads all urls aggregated on a list page"""
    save_page(url)
    for url in extract_urls(filename(url)):        
        save_page(url)

def score_results(directory : str):
    return {f : score(extract_equations(f"{directory}/{f}")) for f in os.listdir(directory)}

def scrape():
    url1 = "https://en.wikipedia.org/wiki/Lists_of_physics_equations"
    url2 = "https://en.wikipedia.org/wiki/List_of_equations"
    url3 = "https://en.wikipedia.org/wiki/List_of_scientific_equations_named_after_people"

    urls = [url2, url3]
    
    for u in urls:
        download_list_page(u)
        
    res = score_results("content")    
    with open('data.json', 'w') as fp:
        json.dump(res, fp)
        
    data_filtered = { x : y for x,y in data.items() if y is not None}    
    with open('data_filtered.json', 'w') as fp:
        json.dump(data_filtered, fp)

def analyze():
    with open('data_filtered.json', 'r') as fp:
        data = json.load(fp)

    
    
if __name__ == "__main__":
    # scrape()
    analyze()
