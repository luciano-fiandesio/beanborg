# -*- coding: utf-8 -*-

import csv
import os
from typing import Dict, List

def init_decision_table(file, debug = False):
    table: Dict[str, List[Tuple]] = {} 
    tablefile = os.path.join(os.getcwd(), file)
    if not os.path.isfile(tablefile) or os.stat(file).st_size == 0:
        if debug: print("The decision table file: " + file + " is missing or empty.")
    else:
        with open(tablefile) as csv_file:
            csv_reader = csv.reader(decomment(csv_file), delimiter=";")
            next(csv_reader)  # skip first line
            for row in csv_reader:
                if any(row):
                    key = row[0]
                    if len(row) == 3 or len(row) == 4:
                        if key not in table:
                            table[key] = []
                        table[key].append(tuple(row[1:]))
                    else:
                        print("invalid rule: " + ", ".join(row))
    return table

def decomment(csvfile):
    for row in csvfile:
        raw = row.split('#')[0].strip()
        if raw: yield row

def resolve_from_decision_table(table, string, default, account=None):
    eq_check_func = {
        "equals": _equals,
        "equals_ic": _equals_ignore_case,
        "startsWith": _startsWith,
        "endsWith": _endsWith,
        "contains": _contains,
        "contains_ic": _contains_ignore_case,
        
        "eq": _equals,
        "sw": _startsWith,
        "ew": _endsWith,
        "co": _contains
    }
    
    for val in table.keys():
        # Sort the list of tuples by the number of elements in each tuple (in descending order)
        t = sorted(table[val], key=lambda x: len(x), reverse=True)
    
        for value in t:
            eq_check_type = value[0]
            if len(value) == 3 and account is not None:
                if eq_check_func.get(eq_check_type)(string, val) and account == value[2]:
                    return value[1]
            elif len(value) == 2:
                if eq_check_func.get(eq_check_type)(string, val):
                    return value[1]
            else:
                print("ignore row from rule file: " + str(value))

    return default

def _equals(string_a, string_b):
    return string_a == string_b

def _equals_ignore_case(string_a, string_b):
    return string_a.casefold() == string_b.casefold()

def _startsWith(string_a, string_b):
    return string_a.startswith(string_b)

def _endsWith(string_a, string_b):
    return string_a.endswith(string_b)

def _contains(string_a, string_b):
    return string_b in string_a 

def _contains_ignore_case(string_a, string_b):
    return string_b.casefold() in string_a.casefold() 

