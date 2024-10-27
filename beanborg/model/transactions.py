# -*- coding: utf-8 -*-


class Transactions:
    """Transactions model."""

    __transactions = {}

    def __init__(self, transactions):
        """Initialize the transactions."""
        self.__transactions = transactions

    def count_no_category(self, default_expense) -> int:
        """Count the number of transactions with no category."""
        txs = []
        for tx in self.__transactions:
            if tx.postings[1].account == default_expense:
                txs.append(tx)

        return len(txs)

    def count(self) -> int:
        """Count the number of transactions."""
        return len(self.__transactions)

    def get_transactions(self):
        """Get the transactions."""
        return self.__transactions
