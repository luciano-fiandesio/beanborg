# -*- coding: utf-8 -*-
from beancount import loader
from beancount.core.data import Transaction
from beancount.core.getters import get_accounts


class JournalUtils:
    """Utility functions for the Beancount journal."""
    @staticmethod
    def _get_entries(journal):
        """Load in-memory all the entries of the provided ledger."""
        entries, _, _ = loader.load_file(journal)
        return entries

    @staticmethod
    def transaction_hashes(journal):
        """Load in-memory all the hashes (md5 property) of the provided ledger.

        This is required for the duplication detecting algo
        """
        md5s = []
        entries = JournalUtils._get_entries(journal)
        for entry in entries:
            if isinstance(entry, Transaction):
                md5 = entry.meta.get("md5", "")
                if md5:
                    md5s.append(md5)
        return md5s

    @staticmethod
    def get_accounts(journal):
        """Get all accounts from the provided ledger."""
        return get_accounts(JournalUtils._get_entries(journal))

    @staticmethod
    def get_transactions_by_account_name(journal, account):
        """Get all transactions for a given account name."""
        entries = JournalUtils._get_entries(journal)
        txs = []
        for entry in entries:
            if isinstance(entry, Transaction):
                if str(entry.meta["filename"]).endswith(f"{account}.ldg"):
                    txs.append(entry)
        return txs
