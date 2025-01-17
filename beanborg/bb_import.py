#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2024  Luciano Fiandesio"
__license__ = "GNU GPLv2"


from beanborg.importer import Importer


def main():
    imp = Importer()
    imp.import_transactions()


if __name__ == "__main__":
    main()
