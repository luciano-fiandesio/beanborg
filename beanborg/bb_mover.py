#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2021  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import glob
import os
import sys
from subprocess import check_call, CalledProcessError

from beanborg.arg_parser import eval_args
from beanborg.config import init_config

def main():
    
    args = eval_args('Move bank csv file to processing folder')
    config = init_config(args.file, args.debug)
    current_dir = os.getcwd()

    if not os.path.isdir(config.csv.download_path):
        print("folder: %s does not exist!"%(config.csv.download_path))
        sys.exit(-1)

    if not os.path.isdir(config.csv.target):
        os.mkdir(config.csv.target)

    # count number of files starting with:
    file_count = len(glob.glob1(config.csv.download_path, config.csv.name + "*"))

    if file_count > 1:
        print("more than one file starting with %s found in %s. Can not continue."%(config.csv.name,config.csv.download_path))
        sys.exit(-1)

    if file_count == 0:
        print("No file found in %s with name starting with: %s"%(config.csv.download_path, config.csv.name))
        sys.exit(-1)

    if config.csv.post_script_path and not os.path.isfile(config.csv.post_script_path):
        print("No post-move script found: %s"%(config.csv.post_script_path))
        sys.exit(-1)    
        
    for f in os.listdir(config.csv.download_path):
        if f.startswith(config.csv.name):
            moved_csv = os.path.join(config.csv.target, config.csv.ref + ".csv")
            os.rename(config.csv.download_path + "/" + f, moved_csv)
            if config.csv.post_script_path:
                try:
                    check_call([config.csv.post_script_path, os.path.join(current_dir, moved_csv)])
                except CalledProcessError as e:
                    print("An error occurred executing: %s\n%s"%(config.csv.post_script_path, str(e)))
    print("Done :) ")


if __name__ == "__main__":
    main()
