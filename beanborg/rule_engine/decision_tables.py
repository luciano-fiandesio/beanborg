#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os


def init_decision_table(file):
    table = {}
    if not os.path.isfile(os.getcwd() + "/" + file):
        print("The decision table file: " + file + " is missing.")
    else:
        with open(os.getcwd() + "/" + file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";")
            next(csv_reader)  # skip first line
            for row in csv_reader:
                if any(row):
                    if len(row) == 3:
                        table[row[0]] = (row[1], row[2])
                    else:
                        print("invalid rule: " + ", ".join(row))
    return table


def resolve_from_decision_table(table, string, default):
    eq_check_func = {
        "equals": _equals,
        "startsWith": _startsWith,
        "endsWith": _endsWith,
        "contains": _contains,
        "eq": _equals,
        "sw": _startsWith,
        "ew": _endsWith,
        "co": _contains
    }
    for k in table.keys():
        t = table[k]
        eq_check = t[0]
        if eq_check_func.get(t[0])(string, k):
            return t[1]

    return default


def _equals(string_a, string_b):
    return string_a == string_b


def _startsWith(string_a, string_b):
    return string_a.startswith(string_b)


def _endsWith(string_a, string_b):
    return string_a.endswith(string_b)

def _contains(string_a, string_b):
    return string_b in string_a 
