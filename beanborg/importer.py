# -*- coding: utf-8 -*-
import csv
import os
import sys
from random import SystemRandom
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from rich import print as rprint
from rich.table import Table
from beancount.parser.printer import format_entry
from beancount.core.data import Amount
from beanborg.arg_parser import eval_args
from beanborg.config import init_config
from beanborg.handlers.amount_handler import AmountHandler
from beanborg.rule_engine.Context import Context
from beanborg.rule_engine.rules_engine import RuleEngine
from beanborg.utils.hash_utils import hash
from beanborg.utils.duplicate_detector import (
    init_duplication_store,
    hash_tuple,
    to_tuple,
    print_duplication_warning,
)
from beanborg.classification.classifier_gpt import Classifier
from beanborg.model.transactions import Transactions
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

    def generate_random_datetime(self, min_year=1900, max_year=datetime.now().year):
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

        if len(self.args.rules.ruleset) > 1 \
                and not os.path.isfile(folder + "/asset.rules") \
                and self.args.rules.account is None \
                and self.args.rules.origin_account is None:

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
            table.add_row("error", str(
                self.stats.error), style="red")
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
            '[red]warning[/red]: '
            'a transaction with identical hash exists in '
            'the journal: '
            f'[bold]{md5}[/bold]')
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
        if len(self.accounts) > 1 and len(self.txs.getTransactions()) > 0:
            rprint(
                '[red]Expecting only one account in csv'
                f'file, found: {str(len(self.accounts))}[/red]'
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
                    pre_trans.append(self.txs.getTransactions()[key])
            else:
                pre_trans.append(self.txs.getTransactions()[key])

        return Transactions(pre_trans)

    def write_tx(self, file_handler, tx):
        file_handler.write(format_entry(tx) + "\n")

    def write_to_ledger(self, account_file, transactions):

        with open(account_file, "a") as exc:
            for tx in transactions:
                self.write_tx(exc, tx)

    def import_transactions(self):
        options = eval_args("Parse bank csv file and import into beancount")
        self.args = init_config(options.file, options.debug)
        import_csv = self.get_import_csv_path()
        self.validate_import_csv(import_csv)
        rule_engine = self.init_rule_engine()
        tx_hashes = JournalUtils().transaction_hashes(self.args.rules.bc_file)
        self.process_csv_file(import_csv, rule_engine, tx_hashes)
        self.post_process_transactions()

    def get_import_csv_path(self):
        return os.path.join(self.args.csv.target, self.args.csv.ref + ".csv")

    def validate_import_csv(self, import_csv):
        if not os.path.isfile(import_csv):
            rprint("[red]file: %s does not exist![red]" % (import_csv))
            sys.exit(-1)

    def process_csv_file(self, import_csv, rule_engine, tx_hashes):
        with open(import_csv) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=self.args.csv.separator)
            self.skip_csv_headers(csv_reader)
            for row in csv_reader:
                self.process_csv_row(row, rule_engine, tx_hashes)

    def skip_csv_headers(self, csv_reader):
        for _ in range(self.args.csv.skip):
            next(csv_reader)

    def process_csv_row(self, row, rule_engine, tx_hashes):
        self.stats.tx_in_file += 1
        try:
            md5 = hash(row)
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

    def post_process_transactions(self):
        self.verify_accounts_count()
        working_account = self.get_working_account()
        filtered_txs = self.verify_unique_transactions(working_account)
        self.stats.skipped_by_user = self.txs.count() - filtered_txs.count()
        self.stats.processed = filtered_txs.count()
        if self.should_classify_transactions(filtered_txs):
            Classifier().classify(filtered_txs, self.args)
        self.write_transactions_to_ledger(working_account, filtered_txs)
        self.print_summary()

    def get_working_account(self):
        if not self.accounts:
            raise Exception("No accounts found in the CSV file.")
        return self.accounts.pop()

    def should_classify_transactions(self, filtered_txs):
        return (
            self.args.classifier.use_classifier
            and filtered_txs.count_no_category(self.args.rules.default_expense) > 0
        )

    def write_transactions_to_ledger(self, account, transactions):
        account_file = account + ".ldg"
        self.write_to_ledger(account_file, transactions.getTransactions())

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
                "in the config file.")

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
        tx = tx._replace(
            postings=[new_posting] + [tx.postings[1]])

        # add narration
        if self.args.indexes.narration:
            tx = tx._replace(
                narration=row[self.args.indexes.narration].strip())

        if self.debug():
            print(tx)

        return tx

    def process_tx(self, row, md5, rule_engine):
        """
        Process a transaction from a CSV row using the provided rule engine.

        Args:
            row (list): A list representing a row from the CSV file.
            md5 (str): The MD5 hash of the CSV row.
            rule_engine (RuleEngine): An instance of the RuleEngine class.

        Returns:
            None
        """
        tx = rule_engine.execute(row)

        if not tx:
            # If no transaction is returned by the rule engine,
            # increment the ignored_by_rule counter and return early
            self.stats.ignored_by_rule += 1
            return

        # Update the no_category counter if applicable
        self.update_no_category_stats(tx)

        # Parse the transaction date from the CSV row
        tx_date = self.parse_tx_date(row)

        # Validate and enrich the transaction
        tx = self.validate_and_enrich_tx(row, tx, tx_date, md5)

        # Store the processed transaction in the txs dictionary
        self.store_transaction(tx, tx_date)

    def update_no_category_stats(self, tx):
        """
        Update the no_category counter if the transaction lacks a proper category.

        Args:
            tx (Transaction): The transaction object.

        Returns:
            None
        """
        if tx.postings[1].account == self.args.rules.default_expense:
            self.stats.no_category += 1

    def parse_tx_date(self, row):
        """
        Parse the transaction date from the CSV row.

        Args:
            row (list): A list representing a row from the CSV file.

        Returns:
            datetime: The parsed transaction date.
        """
        return datetime.strptime(
            row[self.args.indexes.date].strip(), self.args.csv.date_format
        )

    def validate_and_enrich_tx(self, row, tx, tx_date, md5):
        """
        Validate and enrich the transaction with additional data from the CSV row.

        Args:
            row (list): A list representing a row from the CSV file.
            tx (Transaction): The transaction object.
            tx_date (datetime): The parsed transaction date.
            md5 (str): The MD5 hash of the CSV row.

        Returns:
            Transaction: The validated and enriched transaction.
        """
        tx = self.validate(tx)
        tx = self.enrich(row, tx, tx_date, md5)
        return tx

    def store_transaction(self, tx, tx_date):
        """
        Store the processed transaction in the txs dictionary.

        Args:
            tx (Transaction): The processed transaction object.
            tx_date (datetime): The parsed transaction date.

        Returns:
            None
        """
        key = self.generate_tx_key(tx_date)
        self.txs.getTransactions()[key] = tx

    def generate_tx_key(self, tx_date):
        """
        Generate a unique key for the transaction based on the date and a random time.

        Args:
            tx_date (datetime): The parsed transaction date.

        Returns:
            str: The generated transaction key.
        """
        return str(tx_date) + str(self.generate_random_datetime().time())
