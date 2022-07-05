#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2021  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import csv
import hashlib
import os
import os.path
import random
import sys
import traceback
from datetime import datetime, timedelta

from beancount import loader

from beancount.core.data import Transaction, Amount
from beancount.parser.printer import format_entry
from beanborg.handlers.amount_handler import AmountHandler
from beanborg.arg_parser import eval_args
from beanborg.config import init_config
from beanborg.rule_engine.Context import Context
from beanborg.rule_engine.rules_engine import RuleEngine
from beanborg.utils.duplicate_detector import (
    init_duplication_store,
    hash_tuple,
    to_tuple,
    print_duplication_warning,
)


def gen_datetime(min_year=1900, max_year=datetime.now().year):
    """generate a datetime in format yyyy-mm-dd hh:mm:ss.000000"""
    start = datetime(min_year, 1, 1, 00, 00, 00)
    years = max_year - min_year + 1
    end = start + timedelta(days=365 * years)
    return start + (end - start) * random.random()


def init_rule_engine(args):
    """
    Initialize the import rule engine using the arguments from
    the configuration file
    """

    folder = args.rules.rules_folder

    if len(args.rules.ruleset) > 1:

        if (
            not os.path.isfile(folder + "/asset.rules")
            and args.rules.account is None
            and args.rules.origin_account is None
        ):

            print(
                "Please specify an account in your config file "
                "or create an entry in the asset.rules file"
            )
            sys.exit(-1)

    return RuleEngine(
        Context(
            date_fomat=args.csv.date_format,
            default_expense=args.rules.default_expense,
            date_pos=args.indexes.date,
            payee_pos=args.indexes.counterparty,
            tx_type_pos=args.indexes.tx_type,
            account_pos=args.indexes.account,
            narration_pos=args.indexes.narration,
            account=args.rules.account,
            ruleset=args.rules.ruleset,
            rules_dir=folder,
            force_account=args.rules.origin_account,
            debug=args.debug,
        )
    )


def load_journal_hashes(journal):
    """
    Load in-memory all the hashes (md5 property) of the provided ledger.
    This is required for the duplication detecting algo
    """

    md5s = []
    entries, _, _ = loader.load_file(journal)
    for entry in entries:
        if isinstance(entry, Transaction):
            md5 = entry.meta.get("md5", "")
            if md5:
                md5s.append(md5)
    return md5s


def log_error(row):
    """simple error logger"""
    print("CSV: " + ",".join(row))
    print(
        "------------------------------------------------------------------------------"
    )


def get_account(row, args):
    """get the account value for the given csv line or use the specified account"""
    if args.rules.account:
        return args.rules.account

    return row[args.indexes.account]


def get_currency(row, args):
    """get the currency value for the given csv line or use the specified currency"""
    if args.rules.currency:
        return args.rules.currency
    return row[args.indexes.currency]


def write_tx(file_handler, tx):
    file_handler.write(format_entry(tx) + "\n")


def main():

    options = eval_args("Parse bank csv file and import into beancount")
    args = init_config(options.file, options.debug)

    import_csv = args.csv.target + "/" + args.csv.ref + ".csv"

    if not os.path.isfile(import_csv):
        print("file: %s does not exist!" % (import_csv))
        sys.exit(-1)

    # init report data
    tx_in_file = 0
    processed = 0
    error = 0
    hash_collision = 0
    ignored_by_rule = 0
    transactions = {}
    rule_engine = init_rule_engine(args)
    tx_hashes = load_journal_hashes(args.rules.bc_file)
    # init handlers
    amount_handler = AmountHandler()
    accounts = set()

    with open(import_csv) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=args.csv.separator)
        for _ in range(args.csv.skip):
            next(csv_reader)  # skip the line
        for row in csv_reader:
            tx_in_file += 1
            try:
                if args.debug:
                    print("> processing\n" + str(row))
                md5 = hashlib.md5(",".join(row).encode("utf-8")).hexdigest()
                # keep track of the accounts for each tx:
                # the system expects one account per imported file
                res_account = get_account(row, args)
                if args.debug:
                    print("resolved account: " + str(res_account))
                accounts.add(res_account)

                if md5 not in tx_hashes:
                    tx_date = datetime.strptime(
                        row[args.indexes.date].strip(), args.csv.date_format
                    )
                    tx_meta = {"csv": ",".join(row), "md5": md5}
                    tx = rule_engine.execute(row)

                    if tx:
                        """
                        Handle the origin account: if the tx processed by the
                        rules engin has no origin account, try to assign one
                        from the property file: args.rules.origin_account
                        """
                        if tx.postings[0].account is None:
                            raise Exception(
                                "Unable to resolve the origin account for this transaction, "
                                "please check that the `Replace_Asset` rule "
                                "is in use for this account or set the `origin_account` property "
                                "in the config file."
                            )

                        # replace date """
                        tx = tx._replace(date=str(tx_date.date()))

                        # add md5 and csv """
                        tx = tx._replace(meta=tx_meta)

                        # get a decimal, with the minus sign, if it's an expense
                        amount = amount_handler.handle(
                            row[args.indexes.amount].strip(), args
                        )
                        # add units (how much was spent)
                        new_posting = tx.postings[0]._replace(
                            units=Amount(amount, get_currency(row, args))
                        )
                        tx = tx._replace(postings=[new_posting] + [tx.postings[1]])

                        # add narration
                        tx = tx._replace(narration=row[args.indexes.narration].strip())

                        if args.debug:
                            print(tx)

                        # generate a key based on:
                        # - the tx date
                        # - a random time (tx time is not important, but date is!)
                        transactions[str(tx_date) + str(gen_datetime().time())] = tx
                    else:
                        ignored_by_rule += 1
                else:
                    print(
                        "warning: a transaction with identical hash exists in the journal: "
                        + md5
                    )
                    log_error(row)
                    hash_collision += 1

            except Exception as e:
                print("error: " + str(e))
                log_error(row)
                error += 1
                if args.debug:
                    traceback.print_exc()

        # write transaction to ledger file corresponding to the account id
        if len(accounts) == 1 and transactions:

            account_file = accounts.pop() + ".ldg"
            account_tx = (
                init_duplication_store(account_file, args.rules.bc_file)
                if args.rules.advanced_duplicate_detection
                else {}
            )

            with open(account_file, "a") as exc:
                for key in sorted(transactions):
                    # check if the transaction being imported matches another existing transaction
                    # in the current ledger file.
                    tup = to_tuple(transactions[key])
                    if hash_tuple(tup) in account_tx:
                        if print_duplication_warning(account_tx[hash_tuple(tup)]):
                            write_tx(exc, transactions[key])
                            processed += 1
                    else:
                        write_tx(exc, transactions[key])
                        processed += 1
        else:
            if len(transactions) > 0:
                print(
                    "Expecting only one account in csv file, found: "
                    + str(len(accounts))
                )

    print("\nsummary:\n")
    print("csv tx count: \t\t" + str(tx_in_file))
    print("imported: \t\t" + str(processed))
    print("tx already present: \t" + str(hash_collision))
    print("ignored by rule: \t" + str(ignored_by_rule))
    print("error: \t\t\t" + str(error))


if __name__ == "__main__":
    main()
