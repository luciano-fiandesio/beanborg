#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2024  Luciano Fiandesio"
__license__ = "GNU GPLv2"

from typing import Optional

import fire
from fire.decorators import SetParseFns

from beanborg.importer import Importer


class BeanborgImporter:
    """Parse bank CSV file and import into beancount.

    Synopsis:
        bb_import --config_file=CONFIG_FILE [--debug=true] [--fix_only=true]

    Description:
        Imports bank transactions from CSV files into beancount format.
        Can also fix uncategorized transactions using the --fix-only flag.

    Arguments:
        config_file: Path to the YAML configuration file
        debug: Enable debug output (default: False)
        fix_only: Only fix transactions without an account (default: False)

    Examples:
        bb_import --config_file=config.yaml
        bb_import --config_file=config.yaml --debug=true
        bb_import --config_file=config.yaml --fix_only=true
    """

    @SetParseFns(f=str, config_file=str, debug=bool, fix_only=bool)
    def __call__(
        self,
        f: Optional[str] = None,
        config_file: Optional[str] = None,
        debug: bool = False,
        fix_only: bool = False,
    ):
        """Import transactions from CSV to beancount.

        Args:
            f: Path to the configuration file (shorthand for --config-file)
            config_file: Path to the configuration file
            debug: Enable debug mode
            fix_only: Only fix uncategorized transactions
        """
        final_config_file = f or config_file
        if not final_config_file:
            raise ValueError(
                "Configuration file must be specified using either -f or --config-file"
            )
        imp = Importer()
        return imp.import_transactions(final_config_file, debug, fix_only)


def main():
    """Main function to run the beanborg importer."""
    fire.Fire(BeanborgImporter)
