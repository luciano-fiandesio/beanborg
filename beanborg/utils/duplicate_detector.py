import hashlib

from beancount import loader
from beancount.core.data import Transaction
from rich import print as rprint
from rich.prompt import Confirm


def hash_tuple(tuple):

    m = hashlib.md5()
    for s in tuple:
        m.update(str(s).encode("utf-8"))
    return m.hexdigest()


def to_tuple(transaction):

    return (str(transaction.date), transaction.postings[0].units)


def init_duplication_store(account, journal):
    """
    Builds a map of existing transactions for the account being imported.
    Each map entry has an hash of the value as key and a tuple of
    transaction date and amount value.
    This map is used to report identical transactions being imported,
    should the standard hash based approach fail.
    """
    transactions = {}
    entries, _, _ = loader.load_file(journal)
    for entry in entries:
        if isinstance(entry, Transaction) and entry.meta["filename"].endswith(account):
            tup = to_tuple(entry)
            transactions[hash_tuple(tup)] = tup

    return transactions


def print_duplication_warning(tx):

    rprint(
        "[red]Warning[/red]: a transaction with identical date and"
        " amount already exists in the ledger. "
        f"\ndate: [bold]{tx[0]}[/bold]\namount [bold]{tx[1]}[/bold]"
    )
    return Confirm.ask("Do you want to import it?")
