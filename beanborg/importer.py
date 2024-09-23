# -*- coding: utf-8 -*-
import csv
import os
import re
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from random import SystemRandom

from beancount.core.data import Amount
from beancount.parser.printer import format_entry
from rich import print as rprint
from rich.table import Table

from beanborg.arg_parser import eval_args
from beanborg.classification.classifier import Classifier
from beanborg.config import init_config
from beanborg.handlers.amount_handler import AmountHandler
from beanborg.model.transactions import Transactions
from beanborg.rule_engine.Context import Context
from beanborg.rule_engine.rules_engine import RuleEngine
from beanborg.utils.duplicate_detector import (
    hash_tuple,
    init_duplication_store,
    print_duplication_warning,
    to_tuple,
)
from beanborg.utils.hash_utils import hash
from beanborg.utils.journal_utils import JournalUtils


@dataclass
class ImportStats:
    tx_in_file: int = 0
    processed: int = 0
    error: int = 0
    no_category: int = 0
    hash_collision: int = 0
    ignored_by_rule: int = 0
    skipped_by_user: int = 0


class Importer:
    """
    Initialize the import rule engine using the arguments from
    the configuration file
    """

    def debug(self):
        """check if the importer is started using the debug flag

        Returns:
            boolean: is debug
        """
        return self.args.debug

    def log_error(self, row):
        """simple error logger"""
        print(f'CSV: {",".join(row)}')
        rprint("-" * 80)

    def __init__(self):
        self.stats = ImportStats()
        self.args = None
        self.accounts = set()
        self.txs = Transactions({})

    def gen_datetime(self, min_year=1900, max_year=datetime.now().year):
        """generate a datetime in format yyyy-mm-dd hh:mm:ss.000000"""
        start = datetime(min_year, 1, 1, 00, 00, 00)
        years = max_year - min_year + 1
        end = start + timedelta(days=365 * years)
        return start + (end - start) * SystemRandom.random(self)

    def init_rule_engine(self):
        """
        Initialize the import rule engine using the arguments from
        the configuration file
        """

        folder = self.args.rules.rules_folder

        if (
            len(self.args.rules.ruleset) > 1
            and not os.path.isfile(folder + "/asset.rules")
            and self.args.rules.account is None
            and self.args.rules.origin_account is None
        ):

            rprint(
                "[red]Please specify an account in your config file "
                "or create an entry in the asset.rules file[/red]"
            )
            sys.exit(-1)

        return RuleEngine(
            Context(
                date_fomat=self.args.csv.date_format,
                default_expense=self.args.rules.default_expense,
                date_pos=self.args.indexes.date,
                payee_pos=self.args.indexes.counterparty,
                tx_type_pos=self.args.indexes.tx_type,
                account_pos=self.args.indexes.account,
                narration_pos=self.args.indexes.narration,
                account=self.args.rules.account,
                ruleset=self.args.rules.ruleset,
                rules_dir=folder,
                force_account=self.args.rules.origin_account,
                debug=self.args.debug,
            )
        )

    def print_summary(self):
        table = Table(title="Import Summary")
        table.add_column("Counter", style="magenta")
        table.add_column("Value", style="green", justify="right")
        table.add_row("csv tx count", str(self.stats.tx_in_file))
        table.add_row("imported", str(self.stats.processed))
        table.add_row("tx already present", str(self.stats.hash_collision))
        table.add_row("tx ignored by rule", str(self.stats.ignored_by_rule))
        table.add_row("tx skipped by user", str(self.stats.skipped_by_user))

        if self.stats.error > 0:
            table.add_row("error", str(self.stats.error), style="red")
        else:
            table.add_row("error", str(self.stats.error))
        table.add_row("tx without category", str(self.stats.no_category))
        print("\n")
        rprint(table)

    def get_account(self, row):
        """get the account value for the given csv line
        or use the specified account
        """
        if self.args.rules.account:
            return self.args.rules.account

        return row[self.args.indexes.account]

    def get_currency(self, row):
        """get the currency value for the given csv line or
        use the specified currency
        """
        if self.args.rules.currency:
            return self.args.rules.currency
        return row[self.args.indexes.currency]

    def warn_hash_collision(self, row, md5):
        rprint(
            "[red]warning[/red]: "
            "a transaction with identical hash exists in "
            "the journal: "
            f"[bold]{md5}[/bold]"
        )
        self.log_error(row)
        self.stats.hash_collision += 1

    def fetch_account_transactions(self, account):

        account_file = account + ".ldg"
        account_tx = (
            init_duplication_store(account_file, self.args.rules.bc_file)
            if self.args.rules.advanced_duplicate_detection
            else {}
        )
        return account_tx

    def verify_accounts_count(self):
        if len(self.accounts) > 1 and len(self.transactions) > 0:
            rprint(
                "[red]Expecting only one account in csv"
                f"file, found: {str(len(self.accounts))}[/red]"
            )

    def verify_unique_transactions(self, account):

        account_txs = self.fetch_account_transactions(account)
        pre_trans = []
        for key in sorted(self.txs.getTransactions()):
            # check if the transaction being imported matches another
            # existing transaction
            # in the current ledger file.
            tup = to_tuple(self.txs.getTransactions()[key])
            if hash_tuple(tup) in account_txs:
                if print_duplication_warning(account_txs[hash_tuple(tup)]):
                    pre_trans.append(self.txs[key])
            else:
                pre_trans.append(self.txs.getTransactions()[key])

        return Transactions(pre_trans)

    def write_tx(self, file_handler, tx):
        file_handler.write(format_entry(tx) + "\n")

    def write_to_ledger(self, account_file, transactions):

        with open(account_file, "a") as exc:
            for tx in transactions:
                self.write_tx(exc, tx)

    def fix_uncategorized_tx(self):
        """
        Fix uncategorized transactions in the ledger file.
        """

        # Get target account
        account = self.args.rules.account
        txs = JournalUtils().get_transactions_by_account_name(
            self.args.rules.bc_file, account
        )
        # Get the filename of the first transaction
        filename = txs[0].meta["filename"]

        # filter out txs that have already been categorized
        txs = Transactions(
            [
                tx
                for tx in txs
                if tx.postings[1].account == self.args.rules.default_expense
            ]
        )
        Classifier(
            self.args.rules.training_data,
            self.args.rules.use_llm,
            self.args.rules.bc_file,
        ).classify(txs, self.args)

        with open(filename, "r") as file:
            content = file.read()
            for tx in txs.getTransactions():
                self.update_transaction(
                    content, filename, tx.meta["md5"], tx.postings[1].account
                )

    def update_transaction(self, ledger_content, ledger_file, md5, new_category):

        # Find the transaction block with the given md5
        pattern = rf'(.*?md5: "{md5}".*?Expenses:Unknown.*?\n\n)'
        match = re.search(pattern, ledger_content, re.DOTALL)

        if match:
            transaction_block = match.group(1)

            # Replace 'Expenses:Unknown' with the new category
            updated_block = re.sub(
                r"(  Expenses:Unknown)", f"  {new_category}", transaction_block
            )

            # Replace the old block with the updated one
            updated_content = ledger_content.replace(transaction_block, updated_block)

            # Write the updated content back to the file
            with open(ledger_file, "w") as file:
                file.write(updated_content)
        else:
            print(f"Skipping transaction with md5 {md5} not found.")

    def import_transactions(self):

        options = eval_args("Parse bank csv file and import into beancount")
        self.args = init_config(options.file, options.debug)

        if options.fix_only:
            self.fix_uncategorized_tx()
            return

        # transactions csv file to import
        import_csv = os.path.join(self.args.csv.target, f"{self.args.csv.ref}.csv")

        if not os.path.isfile(import_csv):
            rprint("[red]file: %s does not exist![red]" % (import_csv))
            sys.exit(-1)

        rule_engine = self.init_rule_engine()
        tx_hashes = JournalUtils().transaction_hashes(self.args.rules.bc_file)

        with open(import_csv) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=self.args.csv.separator)
            for _ in range(self.args.csv.skip):
                next(csv_reader)  # skip the line
            for row in csv_reader:
                self.stats.tx_in_file += 1
                try:
                    # calculate hash of csv row
                    md5 = hash(row)

                    # keep track of the accounts for each tx:
                    # the system expects one account per imported file
                    res_account = self.get_account(row)
                    if self.debug():
                        print("resolved account: " + str(res_account))
                    self.accounts.add(res_account)

                    if md5 not in tx_hashes:
                        self.process_tx(row, md5, rule_engine)
                    else:
                        self.warn_hash_collision(row, md5)

                except Exception as e:
                    print("error: " + str(e))
                    self.log_error(row)
                    self.stats.error += 1
                    if self.debug():
                        traceback.print_exc()

        self.verify_accounts_count()
        working_account = self.accounts.pop()
        filtered_txs = self.verify_unique_transactions(working_account)

        self.stats.skipped_by_user = self.txs.count() - filtered_txs.count()
        self.stats.processed = filtered_txs.count()

        if filtered_txs.count_no_category(self.args.rules.default_expense) > 0:
            Classifier(
                self.args.rules.training_data,
                self.args.rules.use_llm,
                self.args.rules.bc_file,
            ).classify(filtered_txs, self.args)

        # write transactions to file
        account_file = working_account + ".ldg"
        self.write_to_ledger(account_file, filtered_txs.getTransactions())
        self.print_summary()

    def validate(self, tx):
        """
        Handle the origin account: if the tx processed by the
        rules engin has no origin account, try to assign one
        from the property file: args.rules.origin_account
        """
        if tx.postings[0].account is None:
            raise Exception(
                "Unable to resolve the origin account for this transaction, "
                "please check that the `Replace_Asset` rule "
                "is in use for this account or set the "
                " `origin_account` property "
                "in the config file."
            )

        return tx

    def enrich(self, row, tx, tx_date, md5):

        tx_meta = {"csv": ",".join(row), "md5": md5}

        # replace date """
        tx = tx._replace(date=str(tx_date.date()))

        # add md5 and csv """
        tx = tx._replace(meta=tx_meta)

        # get a decimal, with the minus sign,
        # if it's an expense
        amount = AmountHandler().handle(
            row[self.args.indexes.amount].strip(), self.args
        )
        # add units (how much was spent)
        new_posting = tx.postings[0]._replace(
            units=Amount(amount, self.get_currency(row))
        )
        tx = tx._replace(postings=[new_posting] + [tx.postings[1]])

        # add narration
        if self.args.indexes.narration:
            tx = tx._replace(narration=row[self.args.indexes.narration].strip())

        if self.debug():
            print(tx)

        return tx

    def process_tx(self, row, md5, rule_engine):

        tx = rule_engine.execute(row)

        if tx:
            # check if the a category is assigned
            if tx.postings[1].account == self.args.rules.default_expense:
                self.stats.no_category += 1

            tx_date = datetime.strptime(
                row[self.args.indexes.date].strip(), self.args.csv.date_format
            )

            tx = self.validate(self.enrich(row, tx, tx_date, md5))

            # generate a key based on:
            # - the tx date
            # - a random time (tx time is not important, but date is!)
            key = str(tx_date) + str(self.gen_datetime().time())
            self.txs.getTransactions()[key] = tx

        else:
            self.stats.ignored_by_rule += 1
