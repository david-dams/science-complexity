# https://github.com/sympy/sympy/issues/26128
# TEXTCMD{...}

import re

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

def get_line(csv_file, line):
    with open(csv_file, "r") as f:
        reader = csv.reader(f, delimiter=',')
        for i, row in enumerate(reader):
            if i == line:
                return row[1]

def strip_garbage(eq_string):
    pruned = eq_string.replace("{\\displaystyle", "")[:-1].replace("\\ell", "l")
    pruned = re.sub(r"\.\s*", "", pruned)
    pruned = re.sub(r"\.\s*", "", pruned)
    pruned = re.sub(r"\\{", "", pruned)
    pruned = re.sub(r"\\}", "", pruned)
    pruned = re.sub(r"\\tilde", "", pruned)
    pattern = r"\\mathrm|\\mathcal\s*\{([^}]*)\}"
    pattern = r"\\mathrm|\\mathcal\s*\{([^}]*)\}"
    pruned = re.sub(pattern, r"\1", pruned)
    
    pattern = r"\{\s*\{|\}\s*\}"
    replacement = lambda m: "{" if "{" in m.group(0) else "}"
    pruned = re.sub(pattern, replacement, pruned)
    
    return pruned

with open("latex.lark", encoding="utf-8") as f:
    latex_grammar = f.read()

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
# expr = "\int f(x) dx = 1"
# expr = "F={\\frac {a^{2}}{L\lambda }}"
# tree = parser.parse(expr)
# print(tree.pretty())

# build parser line by fucking line
line = get_line("sketch.csv", 6)
line_stripped = strip_garbage(line)
# print(parser.parse("\\sup_{1}(1)").pretty())
# foo = r"{\frac {\pi }{2}} t^2"
# print(parser.parse(foo).pretty())
# l = r"f^d"
print(parser.parse(line_stripped).pretty())

# counter = 0
# for i in range(2061):
#     l = get_line("sketch.csv", i)
#     l = strip_garbage(l)
#     try:
#         x = parser.parse(l).pretty()
#     except:
#         counter+=1

# ts _{0}^{z}\cos {\left({\frac {\pi }{2}}t^{2}\right)}d t

# this useful len([t for t in tree.scan_values(lambda v: isinstance(v, Token))])

# https://github.com/cortex-js/compute-engine
# https://github.com/brucemiller/LaTeXML
