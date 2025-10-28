# Science Complexity

Trends in algorithmic complexity of mathematical equations.

## Overview

This project investigates whether the *structural complexity* of mathematical equations has changed over time.  
Named equations were collected from [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page), parsed into symbolic trees using [LaTeXML](https://github.com/brucemiller/LaTeXML), and analyzed for complexity metrics.

Complexity is defined in terms of:
- **Tree depth**
- **Number of nodes**

## Methods

1. **Data collection:** SPARQL query (`query.sparql`) of all named equations and their associated peoples’ birth years.  
2. **Parsing:** Conversion from LaTeX to XML tree structures via LaTeXML.  
3. **Analysis:**  
   - OLS regression  
   - ADF and KPSS tests  
   - KPSS on differenced series  

## Repository Structure

| File | Description |
|------|--------------|
| `process.py` | Main processing and analysis script |
| `query.sparql` | Wikidata query for named equations |
| `raw.json` | Output of the query (as of 18 Jan 2025) |
| `data.tex` | Extracted equations in LaTeX format |
| `data.xml` | Parsed XML representation generated via LaTeXML |

## Reproduction

1. Install [LaTeXML](https://github.com/brucemiller/LaTeXML).  
2. Run:

   ```bash
   python process.py --new
