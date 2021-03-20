#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2021  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import argparse
import csv
import os
from datetime import datetime
import sys
import shutil
from config import *

def main():

    config = init_config("Archives imported CVS file")
    
    target_csv = config.csv.target + '/' + config.csv.ref + ".csv"

    if not os.path.isfile(target_csv):
        sys.exit("file: " + target_csv + " does not exist!")

    if not os.path.isdir(config.csv.archive):
        os.mkdir(config.csv.archive_path)

    dates = []
    print(u"\u2713" + " detecting start and end date of transaction file...")
    with open(target_csv) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=config.csv.separator)
        for i in range(config.csv.skip):
            next(csv_reader)  # skip the line

        for row in csv_reader:
            try:
                dates.append(
                    datetime.strptime(row[config.indexes.date].strip(), config.csv.date_format)
                )
            except Exception as ex:
                print("error: " + str(ex))

    print(u"\u2713" + " moving file to archive...")
    os.rename(
        target_csv,
        config.csv.archive
        + "/"
        + config.csv.ref
        + "_"
        + str(min(dates).date())
        + "_"
        + str(max(dates).date())
        + ".csv",
    )

    print(u"\u2713" + " removing temp folder")
    shutil.rmtree(config.csv.target)


if __name__ == "__main__":
    main()
