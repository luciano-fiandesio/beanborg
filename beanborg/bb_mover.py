#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2023  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import glob
import os
import sys
from subprocess import check_call, CalledProcessError
from rich import print as rprint
from beanborg.arg_parser import eval_args
from beanborg.config import init_config


def main():

    args = eval_args("Move bank csv file to processing folder")
    config = init_config(args.file, args.debug)
    current_dir = os.getcwd()
    # support path like ~/Downloads
    path = os.path.expanduser(config.csv.download_path)
    if not os.path.isdir(path):
        rprint(f'[red]folder: {config.csv.download_path} does not exist![/red]')
        sys.exit(-1)

    if not os.path.isdir(config.csv.target):
        os.mkdir(config.csv.target)

    # count number of files starting with:
    file_count = len(
        glob.glob1(
            path,  
            config.csv.name +
            "*"))

    if file_count > 1:
        print(
            "more than one file starting with %s found in %s. Can not continue." %
            (config.csv.name, config.csv.download_path))
        sys.exit(-1)

    if file_count == 0:
        rprint(
            f'[red]No file found in [bold]{config.csv.download_path}[/bold] ' \
            f'with name starting with: [bold]{config.csv.name}[/bold][/red]'
        )
        sys.exit(-1)

    if config.csv.post_script_path and not os.path.isfile(
            config.csv.post_script_path):
        print("No post-move script found: %s" % (config.csv.post_script_path))
        sys.exit(-1)

    for f in os.listdir(path):
        if f.startswith(config.csv.name):
            moved_csv = os.path.join(
                config.csv.target, config.csv.ref + ".csv")
            os.rename(path + "/" + f, moved_csv)
            if config.csv.post_script_path:
                try:
                    check_call(
                        [
                            config.csv.post_script_path,
                            os.path.join(current_dir, moved_csv),
                        ]
                    )
                except CalledProcessError as e:
                    rprint(
                        "[red]An error occurred executing: %s\n%s[/red]"
                        % (config.csv.post_script_path, str(e))
                    )
    print("Done :) ")


if __name__ == "__main__":
    main()
