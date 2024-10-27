#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2024  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import csv
import os
import shutil
import sys
from datetime import datetime
from typing import Optional

import fire
from fire.decorators import SetParseFns
from rich import print as rprint

from beanborg.config import init_config


class BeanborgArchiver:
    """Archive imported CSV files with date range in filename.

    Synopsis:
        bb_archive --config_file=CONFIG_FILE [--debug=true]

    Description:
        Archives processed CSV files by moving them to an archive directory.
        The archived filename includes the date range of transactions contained
        in the file.

    Arguments:
        config_file: Path to the YAML configuration file
        debug: Enable debug output (default: False)

    Examples:
        bb_archive --config_file=config.yaml
        bb_archive --config_file=/path/to/config.yaml --debug=true
    """

    @SetParseFns(f=str, config_file=str, debug=bool)
    def __call__(
        self,
        f: Optional[str] = None,
        config_file: Optional[str] = None,
        debug: bool = False,
    ):
        """Archive the processed CSV file.

        Args:
            f: Path to the configuration file (shorthand for --config-file)
            config_file: Path to the configuration file
            debug: Enable debug mode

        Returns:
            int: 0 for success, 1 for failure
        """
        final_config_file = f or config_file
        if not final_config_file:
            raise ValueError(
                "Configuration file must be specified using either -f or --config-file"
            )
        config = init_config(final_config_file, debug)

        target_csv = os.path.join(config.csv.target, config.csv.ref + ".csv")

        if not os.path.isfile(target_csv):
            rprint(f"[red]file: {target_csv}  does not exist![red]")
            sys.exit(-1)

        if not os.path.isdir(config.csv.archive):
            os.mkdir(config.csv.archive)

        dates = []
        print("\u2713" + " detecting start and end date of transaction file...")
        with open(target_csv) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=config.csv.separator)
            for _ in range(config.csv.skip):
                next(csv_reader)  # skip the line

            for row in csv_reader:
                try:
                    dates.append(
                        datetime.strptime(
                            row[config.indexes.date].strip(), config.csv.date_format
                        )
                    )
                except Exception as ex:
                    print("error: " + str(ex))

        print("\u2713" + " moving file to archive...")
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

        print("\u2713" + " removing temp folder")
        shutil.rmtree(config.csv.target)


def main():
    """Main function to run the beanborg archiver."""
    fire.Fire(BeanborgArchiver)
