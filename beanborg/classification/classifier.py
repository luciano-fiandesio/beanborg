# -*- coding: utf-8 -*-

from rich.prompt import Confirm
from beancount.parser.printer import format_entry
import os
import pandas as pd
import re
from textblob.classifiers import NaiveBayesClassifier
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from beanborg.utils.journal_utils import JournalUtils
from beancount.core.data import Posting
from beanborg.utils.string_utils import StringUtils


class Classifier:

    def __init__(self, data="training_data.csv"):
        self.trainingDataFile = data

        if os.path.exists(data):
            self.prev_data = pd.read_csv(self.trainingDataFile,
                                         dtype={'amount': 'float64'})
        else:
            self.prev_data = pd.DataFrame(
                columns=['date', 'desc', 'amount', 'cat'])

        self.classifier = NaiveBayesClassifier(
            self._get_training(self.prev_data))

    def has_no_category(self, tx, args) -> bool:

        return tx.postings[1].account == args.rules.default_expense

    def classify(self, txs, args):

        account_completer = FuzzyWordCompleter(
            JournalUtils().get_accounts(args.rules.bc_file))
        # self.classifier.show_informative_features(20)

        if Confirm.ask(
                f'\n[red]you have \
                    [bold] \
                        {txs.count_no_category(args.rules.default_expense)} \
                            [/bold] transactions without category, \
                                do you want to fix them now?[/red]'):

            for i, tx in enumerate(txs.getTransactions()):
                guess = args.rules.default_expense

                if self.has_no_category(tx, args):

                    stripped_text = StringUtils.strip_digits(tx.payee.upper())

                    if len(self.classifier.train_set) > 1:
                        guess = self.classifier.classify(stripped_text)

                    # show the transaction on screen
                    print(format_entry(tx))
                    text = prompt(
                        'Enter account: ',
                        completer=account_completer,
                        complete_while_typing=True,
                        default=guess)

                    if text != guess and text != args.rules.default_expense:
                        # guess was wrong, add to training set and update model
                        # print(tx)
                        just_numbers = re.sub(
                            "[^0-9\\.-]", "", str(tx.postings[0].units))
                        df = pd.DataFrame(
                            {"date": tx.date,
                             "desc": StringUtils.strip_digits(
                                 tx.payee.upper()),
                             "amount": just_numbers,
                             "cat": [text]
                             })
                        df = df.astype(
                            {"desc": str, "date": str, "amount": float})
                        self.classifier.update([(stripped_text, text)])
                        # save training data
                        df.to_csv(self.trainingDataFile, mode='a',
                                  header=False, index=False)

                    else:
                        self.classifier.update([(stripped_text, guess)])

                    posting = Posting(text, None, None, None, None, None)
                    new_postings = [tx.postings[0]] + [posting]
                    txs.getTransactions()[i] = tx._replace(
                        postings=new_postings)

    def _get_training(self, df):
        """Get training data for the classifier, consisting of tuples of
        (text, category)"""
        train = []
        subset = df[df['cat'] != '']
        for i in subset.index:
            row = subset.iloc[i]
            new_desc = StringUtils.strip_digits(row['desc'])
            train.append((new_desc, row['cat']))

        return train

    # def _extractor(self, doc):
    #     """Extract tokens from a given string"""
    #     # TODO: Extend to extract words within words
    #     # For example, MUSICROOM should give MUSIC and ROOM
    #     tokens = self._split_by_multiple_delims(doc, [' ', '/'])

    #     features = {}

    #     for token in tokens:
    #         if token == "" or len(token) < 4:
    #             continue
    #         features[token] = True

    #     return features

    def _split_by_multiple_delims(self, string, delims):
        """Split the given string by the list of delimiters given"""
        regexp = "|".join(delims)

        return re.split(regexp, string)
