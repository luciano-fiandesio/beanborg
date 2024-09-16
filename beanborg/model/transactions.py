# -*- coding: utf-8 -*-


class Transactions:
    __transactions = {}

    def __init__(self, transactions):
        self.__transactions = transactions

    def count_no_category(self, default_expense) -> int:
        txs = []
        for tx in self.__transactions:
            if tx.postings[1].account == default_expense:
                txs.append(tx)

        return len(txs)

    def count(self) -> int:
        return len(self.__transactions)

    def getTransactions(self):
        return self.__transactions
