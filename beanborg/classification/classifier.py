# -*- coding: utf-8 -*-

from rich.prompt import Confirm
from beancount.parser.printer import format_entry
import pandas as pd
import re
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
from openai import OpenAI
from rich.console import Console
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion
from rich.panel import Panel
from rich.layout import Layout
from rich import box
from rich.live import Live
from rich.text import Text

# https://matt.sh/python-project-structure-2024
class Classifier:

    
    def __init__(self, data="tmp/training_data.csv"):
        self.trainingDataFile = data

        training_data = DataLoader.load_data(self.trainingDataFile)

        X = training_data[["desc", "day_of_month", "day_of_week"]]
        y = training_data["cat"]

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


    def display_transaction(self, tx, top_labels, top_probs, chatgpt4_prediction):
        console = Console()
        console.clear()

        # Transaction panel
        tx_panel = Panel(
            format_entry(tx),
            title="Transaction",
            width=80,
            expand=False,
            border_style="cyan",
            box=box.ROUNDED
        )

        # Predictions panel
        predictions_content = ["Top 3 predictions:"]
        for i, (label, prob) in enumerate(zip(top_labels, top_probs), 1):
            predictions_content.append(f"[bold cyan]{i}.[/] [cyan]{label}[/] ({prob:.2f})")
        predictions_content.append(f"[bold cyan]4.[/] ChatGPT-4: [cyan]{chatgpt4_prediction}[/]")
    
        pred_panel = Panel(
            "\n".join(predictions_content),
            title="Predictions",
            width=80,
            expand=False,
            border_style="magenta",
            box=box.ROUNDED
        )
        
        # Print panels
        console.print(tx_panel)
        console.print(pred_panel)
        
    def classify(self, txs, args):

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
                    # Get predictions
                    day_of_month = self.get_day_of_month(tx.date)
                    day_of_week = self.get_day_of_week(tx.date)
                    top_labels, top_probs, chatgpt4_prediction = self.get_top_n_predictions(
                        self.model, self.label_encoder.classes_, stripped_text, day_of_month, day_of_week
                    )

                    while True:
                        self.display_transaction(tx, top_labels, top_probs, chatgpt4_prediction)

                        selected_number = input("Enter your selection (or 'q' to quit): ")
                        if selected_number.lower() == 'q':
                            return  # Exit the function if user wants to quit
                        if selected_number.isdigit():
                            selected_number = int(selected_number)
                            if selected_number == 4:
                                selected_prediction = chatgpt4_prediction
                            elif 1 <= selected_number <= 3:
                                selected_prediction = top_labels[selected_number - 1]
                            else:
                                selected_prediction = None
                            
                            if selected_prediction:
                                text = selected_prediction
                            else:
                                text = guess
                        else:
                            account_completer = CustomFuzzyWordCompleter(
                                JournalUtils().get_accounts(args.rules.bc_file))                        
                      
                            # Create custom key bindings
                            kb = KeyBindings()

                            @kb.add(Keys.Backspace)
                            def _(event):
                                """
                                When backspace is pressed, delete the character and then
                                run auto-completion.
                                """
                                # Delete the character behind the cursor
                                event.current_buffer.delete_before_cursor(count=1)
                                
                                # Run auto-completion
                                event.current_buffer.start_completion(select_first=False)
                            
                            text = prompt(
                                'Enter account: ',
                                completer=account_completer,
                                complete_while_typing=True,
                                key_bindings=kb,
                                default=guess)
                            
                            # if text != guess and text != args.rules.default_expense:
                            #     # guess was wrong, add to training set and update model
                            #     just_numbers = re.sub(
                            #         "[^0-9\\.-]", "", str(tx.postings[0].units))
                            #     df = pd.DataFrame(
                            #         {"date": tx.date,
                            #         "desc": StringUtils.strip_digits(
                            #             tx.payee.upper()),
                            #         "amount": just_numbers,
                            #         "cat": [text]
                            #         })
                            #     df = df.astype(
                            #         {"desc": str, "date": str, "amount": float})
                            #     self.classifier.update([(stripped_text, text)])
                            #     # save training data
                            #     df.to_csv(self.trainingDataFile, mode='a',
                            #             header=False, index=False)
                            # else:
                            #     self.classifier.update([(stripped_text, guess)])
                   

                        posting = Posting(text, None, None, None, None, None)
                        new_postings = [tx.postings[0]] + [posting]
                        txs.getTransactions()[i] = tx._replace(
                            postings=new_postings)
                        
                        break  # Break the loop to move to the next transaction after successful classification
    
    
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
