# -*- coding: utf-8 -*-
from beancount import loader
from beancount.core.data import Transaction
from beancount.core.getters import get_accounts


class JournalUtils:

    def get_entries(self, journal):
        """
        Load in-memory all the entries of the provided ledger.
        """
        entries, _, _ = loader.load_file(journal)
        return entries

    def transaction_hashes(self, journal):
        """
        Load in-memory all the hashes (md5 property) of the provided ledger.
        This is required for the duplication detecting algo
        """

        md5s = []
        entries = self.get_entries(journal)
        for entry in entries:
            if isinstance(entry, Transaction):
                md5 = entry.meta.get("md5", "")
                if md5:
                    md5s.append(md5)
        return md5s

    def get_accounts(self, journal):

        return get_accounts(self.get_entries(journal))

    def get_transactions_by_account_name(self, journal, account):
        """
        Get all transactions for a given account name.
        """
        entries = self.get_entries(journal)
        txs = []
        for entry in entries:
            if isinstance(entry, Transaction):
                if str(entry.meta["filename"]).endswith(f"{account}.ldg"):
                    txs.append(entry)
        return txs
