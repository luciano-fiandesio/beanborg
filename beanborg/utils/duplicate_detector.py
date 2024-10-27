"""Utility module for handling transaction duplicates in Beancount ledgers.

This module provides functionality to detect and handle duplicate transactions
based on transaction dates and amounts. It uses MD5 hashing for quick comparison
and provides interactive confirmation for potential duplicates.
"""

import hashlib
from typing import Any, Dict, Tuple

from beancount import loader
from beancount.core.amount import Amount
from beancount.core.data import Transaction
from rich import print as rprint
from rich.prompt import Confirm


def hash_tuple(transaction_tuple: Tuple[Any, ...]) -> str:
    """Create an MD5 hash from a transaction tuple.

    Args:
        transaction_tuple: Tuple containing transaction data (date and amount)

    Returns:
        str: MD5 hash of the transaction tuple
    """
    hasher = hashlib.md5()
    for element in transaction_tuple:
        hasher.update(str(element).encode("utf-8"))
    return hasher.hexdigest()


def to_tuple(transaction: Transaction) -> Tuple[str, Amount]:
    """Convert a Beancount transaction to a tuple of date and amount.

    Args:
        transaction: Beancount Transaction object

    Returns:
        Tuple containing the transaction date (as string) and amount
    """
    return (str(transaction.date), transaction.postings[0].units)


def init_duplication_store(account: str, journal: str) -> Dict[str, Tuple[str, Amount]]:
    """Build a map of existing transactions for duplicate detection.

    Creates a dictionary where keys are MD5 hashes of transaction tuples
    (date and amount) and values are the original tuples. This is used
    for efficient duplicate detection during import.

    Args:
        account: Account name/identifier to filter transactions
        journal: Path to the Beancount journal file

    Returns:
        Dictionary mapping transaction hashes to (date, amount) tuples
    """
    transactions = {}
    entries, _, _ = loader.load_file(journal)

    for entry in entries:
        if isinstance(entry, Transaction) and entry.meta["filename"].endswith(account):
            transaction_tuple = to_tuple(entry)
            transactions[hash_tuple(transaction_tuple)] = transaction_tuple

    return transactions


def print_duplication_warning(transaction_tuple: Tuple[str, Amount]) -> bool:
    """Display a warning for duplicate transactions and ask for confirmation.

    Args:
        transaction_tuple: Tuple containing transaction date and amount

    Returns:
        bool: True if user wants to import the transaction, False otherwise
    """
    rprint(
        "[red]Warning[/red]: a transaction with identical date and"
        " amount already exists in the ledger. "
        f"\ndate: [bold]{transaction_tuple[0]}[/bold]"
        f"\namount: [bold]{transaction_tuple[1]}[/bold]"
    )
    return Confirm.ask("Do you want to import it?")
