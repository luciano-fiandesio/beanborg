#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2021  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import argparse
import os
import sys
import glob
import yaml
from config import *

def main():
    
    config = init_config("test")
    
    print(config.csv.download_path)
    print(config.csv.name)
    print(config.csv.ref)
    print("amount: " + str(config.indexes.amount))
    print("date: " + str(config.indexes.date))

    print("date format: " + config.rules.date_format)

if __name__ == "__main__":
    main()
