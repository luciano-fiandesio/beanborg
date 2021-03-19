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
    
    config = init_config("Move bank csv file to processing folder")
    
    if not os.path.isdir(config.path):
        print("folder: %s does not exist!"%(config.path,))
        sys.exit(-1)

    if not os.path.isdir(config.target):
        os.mkdir(config.target)

    # count number of files starting with:
    file_count = len(glob.glob1(config.path, config.name + "*"))

    if file_count > 1:
        print("more than one file starting with %s found in %s. Can not continue."%(config.name,config.path))
        sys.exit(-1)

    if file_count == 0:
        print("No file found in %s with name starting with: %s"%(config.path, config.name))
        sys.exit(-1)


    for f in os.listdir(args.folder):
        if f.startswith(args.name):
            os.rename(args.folder + "/" + f, args.target + "/" + args.bank + ".csv")

    print("Done :) ")


if __name__ == "__main__":
    main()
