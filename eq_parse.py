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
    return eq_string.replace("{\\displaystyle", "")[:-1]

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
l = get_line("sketch.csv", 2)
l = strip_garbage(l)
print(parser.parse("\\sup_{1}(1)").pretty())
# foo = "f^{*}1"
# print(parser.parse(foo).pretty())
# l = r"f^d"
print(parser.parse(l).pretty())

# this useful len([t for t in tree.scan_values(lambda v: isinstance(v, Token))])
