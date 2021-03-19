#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2021  Luciano Fiandesio"
__license__ = "GNU GPLv2"

import csv
from datetime import datetime, timedelta
import hashlib
import os
import os.path
import sys
import random
import traceback
from beancount.parser.printer import format_entry
from beancount.core.data import Transaction, Amount
from beancount.core.number import D
import beancount.loader as loader

from rule_engine.rules_engine import RuleEngine
from rule_engine.Context import Context
from rule_engine.decision_tables import init_decision_table


def gen_datetime(min_year=1900, max_year=datetime.now().year):
    """ generate a datetime in format yyyy-mm-dd hh:mm:ss.000000 """
    start = datetime(min_year, 1, 1, 00, 00, 00)
    years = max_year - min_year + 1
    end = start + timedelta(days=365 * years)
    return start + (end - start) * random.random()


def init_rule_engine(args):
    """
    Initialize the import rule engine using the arguments from
    the configuration file
    """

    # make sure the rules folder exists
    if not os.path.isdir(args.rules_folder):
        sys.exit("The rule folder " + args.rules_folder + " does not exist!")

    # make sure the rules files exists
    if not os.path.isfile(args.rules_folder + "/" + args.rules_file):
        sys.exit("The rule file " + args.rules_file + " does not exist!")

    if not os.path.isfile(args.rules_folder + "/asset.rules") and args.account is None:

        print('Please specify an account id string (using the -a flag)'
              'or create an entry in the asset.rules file')

    return RuleEngine(
        Context(
            date_fomat=args.date_format,
            default_expense=args.default_expense,
            date_pos=args.date_pos,
            payee_pos=args.payee_pos,
            tx_type_pos=args.tx_type_pos,
            account_pos=args.account_pos,
            account=args.account,
            rules=args.rules_folder + "/" + args.rules_file,
            rules_dir=args.rules_folder,
            assets=init_decision_table(args.rules_folder + "/asset.rules"),
            accounts=init_decision_table(args.rules_folder + "/account.rules"),
            payees=init_decision_table(args.rules_folder + "/payee.rules"),
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
    """ simple error logger """
    print("CSV: " + ",".join(row))
    print(
        "------------------------------------------------------------------------------"
    )


def get_account(row, args):
    """ get the account value for the given csv line or use the specified account """
    if args.account:
        return args.account

    return row[args.account_pos]


def get_currency(row, args):
    """ get the currency value for the given csv line or use the specified currency """
    if args.currency:
        return args.currency
    return row[args.currency_pos]


def resolve_amount(row, args):
    """
    aaa
    """
    # Get the amount from the line
    val = row[args.amount_pos].strip()

    if args.amount_pos_in != -99:
        return D(row[args.amount_pos_in].strip().replace(args.currency_sep, ".")) -
        D(val.replace(args.currency_sep, "."))

    if args.invert_negative:
        if val[0] == "-":
            val = val.replace("-", "+")

    if args.force_negative == 1:
        if val[0].isdigit():
            val = "-" + val
    return D(val.replace(args.currency_sep, "."))


def main():

    args = init_config("Parse bank csv file and import into beancount")

    if not os.path.isfile(args.file):
        print("file: %s does not exist!" % (args.file))
        sys.exit(-1)

    # init report data
    tx_in_file = 0
    processed = 0
    error = 0
    hash_collision = 0
    ignored_by_rule = 0
    transactions = {}
    rule_engine = init_rule_engine(args)
    tx_hashes = load_journal_hashes(args.beancount_file)

    if args.debug:
        print("found hashes:  " + str(tx_hashes))

    accounts = set()

    with open(args.file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=args.separator)
        for i in range(args.skip):
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
                    print("resolved account: " + res_account)
                accounts.add(res_account)

                if md5 not in tx_hashes:
                    tx_date = datetime.strptime(
                        row[args.date_pos].strip(), args.date_format
                    )
                    tx_meta = {"csv": ",".join(row), "md5": md5}
                    tx = rule_engine.execute(row)

                    if tx:

                        # sreplace date """
                        tx = tx._replace(date=str(tx_date.date()))

                        # add md5 and csv """
                        tx = tx._replace(meta=tx_meta)

                        # get a decimal, with the minus sign, if it's an expense
                        amount = resolve_amount(row, args)

                        # add units (how much was spent)
                        new_posting = tx.postings[0]._replace(
                            units=Amount(amount, get_currency(row, args))
                        )
                        tx = tx._replace(
                            postings=[new_posting] + [tx.postings[1]])

                        if args.debug:
                            print(tx)

                        if tx.postings[0].account is None:
                            raise Exception(
                                'Unable to resolve the account, '
                                'please check that the `Replace_Asset` rule'
                                'is in use for this account'
                            )

                        # generate a key based on:
                        # - the tx date
                        # - a random time (tx time is not important, but date is!)
                        transactions[str(tx_date) +
                                     str(gen_datetime().time())] = tx
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

            with open(accounts.pop() + ".ldg", "a") as exc:
                for key in sorted(transactions):
                    exc.write(format_entry(transactions[key]) + "\n")
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
    print("ignored by rule \t" + str(ignored_by_rule))
    print("error: \t\t\t" + str(error))


if __name__ == "__main__":
    main()
