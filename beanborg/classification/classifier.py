# -*- coding: utf-8 -*-

from rich.prompt import Confirm
from beancount.parser.printer import format_entry
import os
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
from beanborg.utils.journal_utils import JournalUtils
from beancount.core.data import Posting
from beanborg.utils.string_utils import StringUtils
from openai import OpenAI
from rich.console import Console
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion

# https://matt.sh/python-project-structure-2024
class Classifier:

    def load_data(self, filepath):

        # Load CSV data and extract date-related features
        data = pd.read_csv(filepath)
        # Convert 'date' column to datetime and extract day of month
        data["day_of_month"] = pd.to_datetime(data["date"], errors="coerce").dt.day
        # Convert 'date' column to datetime and extract day of week (0-6, where 0 is Monday)
        data["day_of_week"] = pd.to_datetime(data["date"], errors="coerce").dt.dayofweek
        return data

    def __init__(self, data="tmp/training_data.csv"):
        self.trainingDataFile = data

        training_data = self.load_data(self.trainingDataFile)

        X = training_data[["desc", "day_of_month", "day_of_week"]]
        y = training_data["cat"]

        # Encode target labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)

        self.model = self.build_model()
        self.model.fit(X, y_encoded)
        # if os.path.exists(data):
        #     self.prev_data = pd.read_csv(self.trainingDataFile,
        #                                  dtype={'amount': 'float64'})
        # else:
        #     self.prev_data = pd.DataFrame(
        #         columns=['date', 'desc', 'amount', 'cat'])

        # self.classifier = NaiveBayesClassifier(
        #     self._get_training(self.prev_data))

    def has_no_category(self, tx, args) -> bool:

        return tx.postings[1].account == args.rules.default_expense
    
    
    
    def build_model(self):
        column_transformer = ColumnTransformer(
            transformers=[
                ("desc_tfidf", TfidfVectorizer(ngram_range=(1, 3)), "desc"),
            ("day_scaler", MinMaxScaler(), ["day_of_month"]),
            ("day_week_onehot", OneHotEncoder(), ["day_of_week"]),
        ],
        remainder="passthrough",
        )

        pipeline = make_pipeline(
            column_transformer,
            SMOTE(random_state=42, k_neighbors=1),
            SVC(probability=True, kernel="linear", C=1.0),
        )

        return pipeline

    def query_gpt4_for_label(self,description, labels):
        try:
            client = OpenAI()

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are 'TransactionBud' a helpful and concise utility designed to categorize bank transactions efficiently. Your primary function is to assign a category to each transaction presented to you",
                    },
                    {
                        "role": "user",
                        "content": f"Given the description '{description}', what would be the most appropriate category among the following: {', '.join(labels)}? Only output the category name without any additional text.",
                    },
                ],
                temperature=0.7,
                top_p=1,
            )
            return response.choices[0].message.content
            # return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Failed to query GPT-4: {str(e)}")
            return None


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

        alternative_label = self.query_gpt4_for_label(text, labels)
        print(f"Alternative label from ChatGPT-4: {alternative_label}")
        return top_classes, top_probabilities, alternative_label

    def get_day_of_month(self, date):
        return pd.to_datetime(date).day
    
    def get_day_of_week(self, date):
        return pd.to_datetime(date).dayofweek

    def classify(self, txs, args):

        
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
                    # Get predictions
                    day_of_month = self.get_day_of_month(tx.date)
                    day_of_week = self.get_day_of_week(tx.date)
                    top_labels, top_probs, chatgpt4_prediction = self.get_top_n_predictions(
                        self.model, self.label_encoder.classes_, stripped_text, day_of_month, day_of_week
                    )

                    # Initialize rich console
                    console = Console()
                    
                    console.rule()
                    console.print(format_entry(tx))
                    console.rule()
                    # Print predictions with numbers using rich formatting
                    console.print("Top 3 predictions:", style="bold")
                    for i, (label, prob) in enumerate(zip(top_labels, top_probs), 1):
                        console.print(f"[bold cyan]{i}.[/] Label: [bold cyan]{label}[/], Probability: [bold cyan]{prob:.4f}[/]")

                    console.print(f"[bold cyan]4.[/] ChatGPT-4 Prediction: [bold cyan]{chatgpt4_prediction}[/]")

                    # Prompt user to select a prediction
                    selected_number = input("Select a number to choose a prediction: ")
                    
                    if selected_number.isdigit():
                        selected_number = int(selected_number)
                        if selected_number == 4:
                            selected_prediction = chatgpt4_prediction
                        elif 1 <= selected_number <= 3:
                            selected_prediction = top_labels[selected_number - 1]
                        else:
                            selected_prediction = None
                        if selected_prediction:
                            console.print(f"Selected prediction: [bold]{selected_prediction}[/bold]", style="bold green")
                            
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
                        
                        if text != guess and text != args.rules.default_expense:
                            # guess was wrong, add to training set and update model
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
                            # TODO self.classifier.update([(stripped_text, text)])
                            # save training data
                            df.to_csv(self.trainingDataFile, mode='a',
                                    header=False, index=False)
                        else:
                            self.classifier.update([(stripped_text, guess)])
                    # show the transaction on screen
                    #print(format_entry(tx))
                    # text = prompt(
                    #     'Enter account: ',
                    #     completer=account_completer,
                    #     complete_while_typing=True,
                    #     default=guess)

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
