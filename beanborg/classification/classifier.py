# -*- coding: utf-8 -*-

from rich.prompt import Confirm
from beancount.parser.printer import format_entry
import pandas as pd
import numpy as np
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, OneHotEncoder
from sklearn.svm import SVC
from textblob.classifiers import NaiveBayesClassifier
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from beanborg.classification.custom_fuzzy_wordf_completer import CustomFuzzyWordCompleter
from beanborg.classification.data_loader import DataLoader
from beanborg.classification.gpt_service import GPTService
from beanborg.classification.model_builder import ModelBuilder
from beanborg.classification.ui_service import UIService
from beanborg.utils.journal_utils import JournalUtils
from beancount.core.data import Posting
from beanborg.utils.string_utils import StringUtils
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion
from rich.prompt import Confirm


class Classifier:
    
    def __init__(self, data="tmp/training_data.csv"):
        self.trainingDataFile = data

        self.training_data = DataLoader.load_data(self.trainingDataFile)

        X = self.training_data[["desc", "day_of_month", "day_of_week"]]
        y = self.training_data["cat"]

        # Encode target labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)

        self.model = ModelBuilder.build_model()
        self.model.fit(X, y_encoded)

        self.gpt_service = GPTService()
        self.ui_service = UIService()

    def has_no_category(self, tx, args) -> bool:

        return tx.postings[1].account == args.rules.default_expense


    def get_top_n_predictions(self, model, labels, text, day_of_month, day_of_week, n=3):
        # Create a DataFrame for the input text with the same structure as the training data
        data = {
            "desc": [text],
            "day_of_month": [day_of_month],
            "day_of_week": [day_of_week],
        }
        input_df = pd.DataFrame(data)

        # Predict the probabilities for the input DataFrame
        probs = model.predict_proba(input_df)

        # Get the indices of the top n probabilities
        top_indices = np.argsort(probs[0])[-n:][::-1]

        # Map indices to class labels and probabilities
        top_classes = labels[top_indices]
        top_probabilities = probs[0][top_indices]

        alternative_label = self.gpt_service.query_gpt_for_label(text, labels)
        print(f"Alternative label from ChatGPT-4: {alternative_label}")
        return top_classes, top_probabilities, alternative_label

    def get_day_of_month(self, date):
        return pd.to_datetime(date).day
    
    def get_day_of_week(self, date):
        return pd.to_datetime(date).dayofweek

    def confirm_classification(self, txs, args):
        return Confirm.ask(
            f'\n[red]You have [bold]{txs.count_no_category(args.rules.default_expense)}[/bold] '
            f'transactions without category, do you want to fix them now?[/red]'
        )

    def process_transaction(self, tx, index, txs, args):
        stripped_text = StringUtils.strip_digits(tx.payee.upper())
        day_of_month = self.get_day_of_month(tx.date)
        day_of_week = self.get_day_of_week(tx.date)

        top_labels, top_probs, chatgpt_prediction = self.get_predictions(stripped_text, day_of_month, day_of_week)
        self.ui_service.display_transaction(tx, top_labels, top_probs, chatgpt_prediction)

        selected_category = self.get_user_selection(top_labels, chatgpt_prediction, args)
        if selected_category is None:
            return 'quit'
        
        elif selected_category:
            self.update_transaction(tx, index, txs, selected_category)
            amount = tx.postings[0].units.number  # Assuming the first posting contains the transaction amount
            self.update_training_data(tx.date, stripped_text, amount, selected_category, day_of_month, day_of_week)

            return 'continue'

    def get_predictions(self, text, day_of_month, day_of_week):
        return self.get_top_n_predictions(
            self.model, self.label_encoder.classes_, text, day_of_month, day_of_week
        )

    def get_user_selection(self, top_labels, chatgpt_prediction, args):
        while True:
            selected_number = input("Enter your selection (or 'q' to quit): ")
            if selected_number.lower() == 'q':
                return None
            if selected_number.isdigit():
                return self.handle_numeric_selection(int(selected_number), top_labels, chatgpt_prediction)
            return self.handle_custom_input(args)

    def handle_numeric_selection(self, selected_number, top_labels, chatgpt_prediction):
        if selected_number == 4:
            return chatgpt_prediction
        elif 1 <= selected_number <= 3:
            return top_labels[selected_number - 1]
        return None

    def handle_custom_input(self, args):
        account_completer = CustomFuzzyWordCompleter(
            JournalUtils().get_accounts(args.rules.bc_file))
        kb = self.create_key_bindings()
        return prompt(
            'Enter account: ',
            completer=account_completer,
            complete_while_typing=True,
            key_bindings=kb,
            default=args.rules.default_expense)

    def create_key_bindings(self):
        kb = KeyBindings()

        @kb.add(Keys.Backspace)
        def _(event):
            event.current_buffer.delete_before_cursor(count=1)
            event.current_buffer.start_completion(select_first=False)

        return kb

    def update_transaction(self, tx, index, txs, category):
        posting = Posting(category, None, None, None, None, None)
        new_postings = [tx.postings[0]] + [posting]
        txs.getTransactions()[index] = tx._replace(postings=new_postings)
    
    def update_training_data(self, date, description, amount, category, day_of_month, day_of_week):
        # Check if the exact description already exists
        existing_entry = self.training_data[self.training_data['desc'] == description]
        
        if not existing_entry.empty:
            existing_category = existing_entry['cat'].iloc[0]
            if existing_category != category:
                print(f"Description '{description}' already exists with category '{existing_category}'.")
                action = input(
                    "Choose action:\n"
                    "1. Update existing entry\n"
                    "2. Add new entry\n"
                    "3. Skip update\n"
                    "Enter choice (1/2/3): "
                )
                
                if action == '1':
                    self.training_data.loc[self.training_data['desc'] == description, 'cat'] = category
                    print("Existing entry updated.")
                elif action == '2':
                    self._add_new_entry(date, description, amount, category, day_of_month, day_of_week)
                    print("New entry added.")
                else:
                    print("Update skipped.")
                    return
            else:
                print(f"Entry already exists with the same category. Skipping update.")
                return
        else:
            self._add_new_entry(date, description, amount, category, day_of_month, day_of_week)
            print("New entry added.")
        
        # Save updated data
        self.training_data.to_csv(self.trainingDataFile, index=False)
        
        # Retrain the model
        self._retrain_model()

    def _add_new_entry(self, date, description, amount, category, day_of_month, day_of_week):
        new_data = pd.DataFrame({
            'date': [date],
            'desc': [description],
            'amount': [amount],
            'cat': [category],
            'day_of_month': [day_of_month],
            'day_of_week': [day_of_week]
        })
        self.training_data = pd.concat([self.training_data, new_data], ignore_index=True)

    def _retrain_model(self):
        X = self.training_data[["desc", "day_of_month", "day_of_week"]]
        y = self.training_data["cat"]
        y_encoded = self.label_encoder.fit_transform(y)
        self.model.fit(X, y_encoded)

    def classify(self, txs, args):
        if not self.confirm_classification(txs, args):
            return

        for i, tx in enumerate(txs.getTransactions()):
            if self.has_no_category(tx, args):
                result = self.process_transaction(tx, i, txs, args)
                if result == 'quit':
                    break