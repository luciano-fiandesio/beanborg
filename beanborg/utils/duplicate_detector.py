import hashlib
from beancount import loader
from beancount.core.data import Transaction
from beanborg.utils.input import query_yes_no


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
    Each map entry has an hash of the value as key and a tuple of transaction date
    and amount value.
    This map is used to report identical transactions being imported,
    should the standard hash based approach fail.
    """
    transactions = {}
    entries, _, _ = loader.load_file(journal)
    for entry in entries:
        if isinstance(entry, Transaction):
            if entry.meta["filename"].endswith(account):
                tup = to_tuple(entry)
                transactions[hash_tuple(tup)] = tup

    return transactions


def print_duplication_warning(tx):

    print(
        "Warning: a transaction with identical date and amount already exists in the ledger.\
        \ndate: %s\namount %s"
        % (tx[0], tx[1])
    )
    return query_yes_no("Do you want to import it?")
