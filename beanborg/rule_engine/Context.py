# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass
class Context:
    # ruleset
    ruleset: []
    # custom rules folder
    rules_dir: str
    # the date format used in the CSV file
    date_fomat: str
    # the default account (Expense) to use for a the second "leg" of a
    # transaction
    default_expense: str
    # the index of the date field in the csv file
    date_pos: int
    # # the index of the counterparty field in the csv file
    payee_pos: int
    # the index of the transaction type field in the csv file
    tx_type_pos: int
    # the index of the account id field in the csv file
    account_pos: int
    # the index of the narration field in the csv file
    narration_pos: int
    # if the CSV file has no account id, use "account" to lookup the Account
    # Origin when using the Replace_Asset rule
    account: str
    # Force the Account Origin to the value specifed
    force_account: str
    # Output debug info
    debug: bool
