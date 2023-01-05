# -*- coding: utf-8 -*-

from rich.prompt import Confirm
from beancount.parser.printer import format_entry
import pickle
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from beanborg.utils.journal_utils import JournalUtils
from beancount.core.data import Posting
from os.path import exists

class Classifier:

    model = 'categories_model.sav'
    cl = None
    def __init__(self):
        if (exists(self.model)):
            print("loading training data...")
            self.cl = pickle.load(open(self.model, 'rb'))

    def has_no_category(self, tx, args) -> bool:

        return tx.postings[1].account == args.rules.default_expense

    def classify(self, txs, args):

        account_completer = FuzzyWordCompleter(JournalUtils().get_accounts(args.rules.bc_file))

        if Confirm.ask(
                f'\n[red]you have [bold]{txs.count_no_category(args.rules.default_expense)}[/bold] transactions without category, do you want to fix them now?[/red]'):

            for i, tx in enumerate(txs.getTransactions()):
                category = args.rules.default_expense
                if not self.cl == None:
                    category = self.cl.prob_classify(tx.payee).max()

                if self.has_no_category(tx, args):

                    print(format_entry(tx))
                    text = prompt(
                        'Enter account: ',
                        completer=account_completer,
                        complete_while_typing=True, default=category)
                    posting = Posting(text, None, None, None, None, None)
                    new_postings = [tx.postings[0]] + [posting]
                    txs.getTransactions()[i] = tx._replace(postings=new_postings)


