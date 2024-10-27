#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2024  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import glob
import os
import shutil
import sys
from subprocess import CalledProcessError, check_call
from typing import Optional

import fire
from fire.decorators import SetParseFns
from rich import print as rprint

from beanborg.config import init_config


class BeanborgMover:
    """Move a bank CSV file downloaded from the bank's site into a beanborg processing folder.

    Parameters
    ----------
    config_file: str
        Path to the yaml configuration file
    debug: bool
        Enable debug output (default: False)

    Synopsis
    --------
        bb_mover --config_file=CONFIG_FILE [--debug=true]

    Description:
        Processes CSV files downloaded from your bank and moves them to a beanborg
        processing folder. The tool can optionally run a post-processing script
        after moving the file.

    Examples:
        bb_mover --config_file=/path/to/config.yaml
        bb_mover --config_file=config.yaml --debug=true
    """

    @SetParseFns(f=str, config_file=str, debug=bool)
    def __call__(
        self,
        f: Optional[str] = None,
        config_file: Optional[str] = None,
        debug: bool = False,
    ):
        """Move bank's csv file to processing folder.

        Args:
            f: Path to the yaml configuration file (shorthand for --config-file)
            config_file: Path to the yaml configuration file
            debug: Enable debug mode
        """
        # Use either -f or --config-file
        final_config_file = f or config_file
        if not final_config_file:
            raise ValueError(
                "Configuration file must be specified using either -f or --config-file"
            )
        return self._process(final_config_file, debug)

    def _process(self, config_file: str, debug: bool = False):
        config = init_config(config_file, debug)
        current_dir = os.getcwd()
        # support path like ~/Downloads
        path = os.path.expanduser(config.csv.download_path)
        if not os.path.isdir(path):
            rprint(f"[red]folder: {config.csv.download_path} does not exist![/red]")
            sys.exit(-1)

        if not os.path.isdir(config.csv.target):
            os.mkdir(config.csv.target)

        # count number of files starting with:
        file_count = len(glob.glob1(path, config.csv.name + "*"))

        if file_count > 1:
            print(
                f"more than one file starting with {config.csv.name} "
                f"found in {config.csv.download_path}. Cannot continue."
            )
            sys.exit(-1)

        if file_count == 0:
            rprint(
                f"[red]No file found in [bold]{config.csv.download_path}[/bold] "
                f"with name starting with: [bold]{config.csv.name}[/bold][/red]"
            )
            sys.exit(-1)

        if config.csv.post_script_path and not os.path.isfile(
            config.csv.post_script_path
        ):
            print(f"No post-move script found: {config.csv.post_script_path}")
            sys.exit(-1)

        for f in os.listdir(path):
            if f.startswith(config.csv.name):
                src = os.path.join(path, f)
                moved_csv = os.path.join(config.csv.target, config.csv.ref + ".csv")
                if config.csv.keep_original:
                    shutil.copy(src, moved_csv)
                else:
                    os.rename(src, moved_csv)

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
                            f"[red]An error occurred executing: {config.csv.post_script_path}\n{str(e)}[/red]"
                        )
        print("Done :)")


def main():
    """Main function to run the beanborg mover."""
    fire.Fire(BeanborgMover)
