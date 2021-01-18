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

def main():

    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        "-t", "--target", help="Target folder name (e.g. tmp)", required=True
    )
    parser.add_argument("-a", "--archive", help="archive folder", default="archive")
    parser.add_argument(
        "-b", "--bank", help="Target name (e.g. DeutscheBank)", required=True
    )
    parser.add_argument(
        "-l", "--skip", help="Number of lines to skip", default=1, type=int
    )
    parser.add_argument("-d", "--date_pos", help="", default=0, type=int)
    parser.add_argument("-o", "--date_format", help="")
    parser.add_argument("-s", "--separator", help="CSV file separator", default=",")

    args = parser.parse_args()
    target_csv = args.target + "/" + args.bank + ".csv"

    if not os.path.isfile(target_csv):
        sys.exit("file: " + target_csv + " does not exist!")

    if not os.path.isdir(args.archive):
        os.mkdir(args.archive)

    dates = []
    print(u"\u2713" + " detecting start and end date of transaction file...")
    with open(target_csv) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=args.separator)
        for i in range(args.skip):
            next(csv_reader)  # skip the line

        for row in csv_reader:
            try:
                dates.append(
                    datetime.strptime(row[args.date_pos].strip(), args.date_format)
                )
            except Exception as ex:
                print("error: " + str(ex))

    print(u"\u2713" + " moving file to archive...")
    os.rename(
        target_csv,
        args.archive
        + "/"
        + args.bank
        + "_"
        + str(min(dates).date())
        + "_"
        + str(max(dates).date())
        + ".csv",
    )

    print(u"\u2713" + " removing temp folder")
    shutil.rmtree(args.target)


if __name__ == "__main__":
    main()
