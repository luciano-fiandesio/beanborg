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
    for k in table.keys():
        t = table[k]
        if k in string:
            return t[1]

    return default
