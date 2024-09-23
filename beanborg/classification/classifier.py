# -*- coding: utf-8 -*-

import pandas as pd
from beancount.core.data import Posting
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich import print
from rich.prompt import Confirm

from beanborg.classification.custom_fuzzy_wordf_completer import (
    CustomFuzzyWordCompleter,
)
from beanborg.classification.data_loader import DataLoader
from beanborg.classification.gpt_service import GPTService
from beanborg.classification.transaction_model import TransactionModel
from beanborg.classification.ui_service import UIService
from beanborg.utils.journal_utils import JournalUtils
from beanborg.utils.string_utils import StringUtils


class Classifier:

    def __init__(self, data="training_data.csv", use_llm=False, bc_file=None):
        self.trainingDataFile = data
        self.use_llm = use_llm
        self.bc_file = bc_file
        self.training_data = DataLoader.load_data(self.trainingDataFile)
        try:
            self.model = TransactionModel(self.training_data, data)
        except Exception as e:
            print(f"Error initializing TransactionModel: {e}")
            self.model = None

        self.gpt_service = GPTService(self.use_llm)
        self.ui_service = UIService()

    def has_no_category(self, tx, args) -> bool:
        return tx.postings[1].account == args.rules.default_expense

    def get_day_of_month(self, date):
        return pd.to_datetime(date).day

    def get_day_of_week(self, date):
        return pd.to_datetime(date).dayofweek

    def get_predictions(self, text, day_of_month, day_of_week):

        if self.model is None:
            return [], [], self.get_llm_prediction(text)

        # Use the TransactionModel for predictions
        top_labels, top_probs = self.model.predict(text, day_of_month, day_of_week)

        alternative_label = self.get_llm_prediction(text, top_labels)

        return top_labels, top_probs, alternative_label

    def confirm_classification(self, txs, args):
        return Confirm.ask(
            f"\n[red]You have [bold]{txs.count_no_category(args.rules.default_expense)}[/bold] "
            f"transactions without category, do you want to fix them now?[/red]"
        )

    def get_llm_prediction(self, text):

        if self.use_llm:
            # This function queries the GPT service for a label prediction based on the provided text.
            # It uses the available accounts from the journal to help the GPT service make a more informed prediction.
            # If the GPT service is not available, it returns None.
            accounts = JournalUtils().get_accounts(self.bc_file)
            alternative_label = self.gpt_service.query_gpt_for_label(text, accounts)
        else:
            alternative_label = None

        return alternative_label

    def process_transaction(self, tx, index, txs, args):
        stripped_text = StringUtils.strip_digits(tx.payee.upper())
        day_of_month = self.get_day_of_month(tx.date)
        day_of_week = self.get_day_of_week(tx.date)

        top_labels, top_probs, chatgpt_prediction = self.get_predictions(
            stripped_text, day_of_month, day_of_week
        )
        self.ui_service.display_transaction(
            tx, top_labels, top_probs, chatgpt_prediction
        )

        selected_category = self.get_user_selection(
            top_labels, chatgpt_prediction, args
        )
        if selected_category is None:
            return "quit"
        elif selected_category:
            narration = self.get_user_narration()
            self.update_transaction(tx, index, txs, selected_category, narration)
            amount = tx.postings[0].units.number
            if selected_category != args.rules.default_expense:
                if self.model is not None:
                    self.model.update_training_data(
                        tx.date,
                        stripped_text,
                        amount,
                        selected_category,
                        day_of_month,
                        day_of_week,
                    )
                else:
                    row = pd.DataFrame(
                        {
                            "date": [tx.date],
                            "desc": [stripped_text],
                            "amount": [amount],
                            "cat": [selected_category],
                        }
                    )
                    DataLoader.add_training_row(self, self.trainingDataFile, row)

            return "continue"

    def get_user_narration(self):
        narration = input(
            "Enter a comment for the transaction (press Enter to skip): "
        ).strip()
        return narration if narration else None

    def get_user_selection(self, top_labels, chatgpt_prediction, args):
        options = len(top_labels) + (1 if chatgpt_prediction else 0)
        if options == 0:
            return self.handle_custom_input(args)

        while True:
            selected_number = input(
                f"Enter your selection (1-{options}, or 'Enter' to choose the category, 'q' to quit): "
            )
            if selected_number.lower() == "q":
                return None
            if selected_number.isdigit():
                return self.handle_numeric_selection(
                    int(selected_number), top_labels, chatgpt_prediction
                )
            return self.handle_custom_input(args)

    def handle_numeric_selection(self, selected_number, top_labels, chatgpt_prediction):
        if chatgpt_prediction and selected_number == len(top_labels) + 1:
            return chatgpt_prediction
        elif 1 <= selected_number <= len(top_labels):
            return top_labels[selected_number - 1]
        return None

    def handle_custom_input(self, args):
        accounts = JournalUtils().get_accounts(args.rules.bc_file)
        account_completer = CustomFuzzyWordCompleter(accounts)
        kb = self.create_key_bindings()
        selected_category = prompt(
            "Enter account: ",
            completer=account_completer,
            complete_while_typing=True,
            key_bindings=kb,
            default=args.rules.default_expense,
        )
        if selected_category not in accounts:
            print(
                "[bold red]Invalid account. Please select a valid account.[/bold red]"
            )
            return self.handle_custom_input(args)
        return selected_category

    def create_key_bindings(self):
        kb = KeyBindings()

        @kb.add(Keys.Backspace)
        def _(event):
            event.current_buffer.delete_before_cursor(count=1)
            event.current_buffer.start_completion(select_first=False)

        return kb

    def update_transaction(self, tx, index, txs, category, narration=None):
        posting = Posting(category, None, None, None, None, None)
        new_postings = [tx.postings[0]] + [posting]
        new_tx = tx._replace(postings=new_postings)
        if narration:
            new_tx = new_tx._replace(narration=narration)
        txs.getTransactions()[index] = new_tx

    def classify(self, txs, args):
        if not self.confirm_classification(txs, args):
            return

        for i, tx in enumerate(txs.getTransactions()):
            if self.has_no_category(tx, args):
                result = self.process_transaction(tx, i, txs, args)
                if result == "quit":
                    break
