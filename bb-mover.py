#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2020  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import argparse
import os
import sys
import glob


def main():
    parser = argparse.ArgumentParser(
        description='Move bank csv file to processing folder')

    parser.add_argument(
        '-d', '--folder', help='Directory to scan for incoming bank csv file', required=True)
    parser.add_argument(
        '-f', '--name', help='String to identify bank csv file (starts with)', required=True)
    parser.add_argument(
        '-t', '--target', help='Target folder name (e.g. tmp)', default='tmp')
    parser.add_argument(
        '-b', '--bank', help='Target name (e.g. DeutscheBank)', required=True)

    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        sys.exit('file: ' + args.folder + ' does not exist!')

    if not os.path.isdir(args.target):
        os.mkdir(args.target)

    # count number of files starting with:
    file_count = len(glob.glob1(args.folder, args.name + "*"))

    if file_count > 1:
        sys.exit('more than one file starting with: ' +
                 args.name + ' found. Can not continue.')

    if file_count == 0:
        sys.exit('No file found in ' + args.folder +
                 ' with name starting with: ' + args.name)

    for f in os.listdir(args.folder):
        if f.startswith(args.name):
            os.rename(args.folder + '/' + f, args.target +
                      '/' + args.bank + '.csv')

    print("Done :) ")


if __name__ == '__main__':
    main()
