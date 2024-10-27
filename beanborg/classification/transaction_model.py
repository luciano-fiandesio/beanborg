"""Transaction category prediction using machine learning.

This module provides functionality for predicting transaction categories
based on transaction descriptions and temporal features using a KNN classifier
with SMOTE oversampling for handling imbalanced data.
"""

import os
from datetime import date
from typing import Tuple

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler


class TransactionModel:
    """Machine learning model for transaction categorization.

    This class handles the training and prediction of transaction categories
    using a KNN classifier with SMOTE oversampling. It includes functionality
    for model training, prediction, and updating the training dataset.

    Attributes:
        training_data: DataFrame containing training transactions
        data_file: Path to CSV file for storing transaction data
        model: Trained classification pipeline
        label_encoder: Encoder for transaction categories
    """

    def __init__(self, training_data: pd.DataFrame, data_file: str):
        """Initialize the transaction model."""
        self.training_data = training_data
        self.data_file = data_file
        self._create_and_fit_model()

    def _remove_single_sample_classes(
        self, x: pd.DataFrame, y: pd.Series
    ) -> Tuple[pd.DataFrame, pd.Series]:
        class_counts = y.value_counts()
        classes_to_keep = class_counts[class_counts >= 2].index
        mask = y.isin(classes_to_keep)
        return x[mask], y[mask]

    def _create_and_fit_model(self):
        """Create and train the classification pipeline.

        Creates a pipeline with:
        1. Feature processing (text vectorization and scaling)
        2. SMOTE oversampling for handling imbalanced classes
        3. KNN classifier

        """
        x = self.training_data[["desc", "day_of_month", "day_of_week"]]
        y = self.training_data["cat"]

        # Remove classes with only one sample
        x, y = self._remove_single_sample_classes(x, y)

        # Encode target labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)

        # Create feature processing pipeline
        feature_pipeline = ColumnTransformer(
            [
                (
                    "text",
                    make_pipeline(
                        CountVectorizer(analyzer=str.split),  # Removed token_pattern
                        StandardScaler(with_mean=False),
                    ),
                    "desc",
                ),
                ("num", StandardScaler(), ["day_of_month", "day_of_week"]),
            ]
        )

        # Create KNN classifier
        n_neighbors = min(5, len(y) - 1)
        knn = KNeighborsClassifier(n_neighbors=n_neighbors)

        # Create pipeline with SMOTE
        self.model = ImbPipeline(
            [
                ("features", feature_pipeline),
                ("smote", SMOTE(k_neighbors=min(5, min(y.value_counts()) - 1))),
                ("classifier", knn),
            ]
        )

        # Fit the model
        self.model.fit(x, y_encoded)

    def predict(
        self, text: str, day_of_month: int, day_of_week: int, n: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Predict top n categories for a transaction.

        Args:
            text: Transaction description
            day_of_month: Day of month (1-31)
            day_of_week: Day of week (0-6)
            n: Number of top predictions to return

        Returns:
            Tuple of (predicted_categories, prediction_probabilities)

        """
        # Create a DataFrame for the input text with the same structure as the training data
        data = {
            "desc": [text],
            "day_of_month": [day_of_month],
            "day_of_week": [day_of_week],
        }
        input_df = pd.DataFrame(data)

        # Predict the probabilities for the input DataFrame
        probs = self.model.predict_proba(input_df)

        # Get the indices of the top n probabilities
        top_indices = np.argsort(probs[0])[-n:][::-1]

        # Map indices to class labels and probabilities
        top_classes = self.label_encoder.classes_[top_indices]
        top_probabilities = probs[0][top_indices]

        return top_classes, top_probabilities

    def update_training_data(
        self,
        date: date,
        description: str,
        amount: float,
        category: str,
        day_of_month: int,
        day_of_week: int,
    ) -> None:
        """Updates the training data with a new or existing entry and retrains the model."""
        tokenized_description = self._tokenize_description(description)

        # Check if the description already exists
        existing_entry = self.training_data[
            self.training_data["desc"] == tokenized_description
        ]

        if not existing_entry.empty:
            existing_category = existing_entry["cat"].iloc[0]

            if existing_category != category:
                # Conflict found: Ask user how to handle the conflicting category
                self._handle_existing_entry_conflict(
                    tokenized_description,
                    existing_category,
                    date,
                    amount,
                    category,
                    day_of_month,
                    day_of_week,
                )
            else:
                # Entry already exists with the same category, no update needed
                print(
                    f"Entry already exists with category '{existing_category}'. Skipping update."
                )
                return
        else:
            # Add a new entry
            self._add_new_entry(
                date, tokenized_description, amount, category, day_of_month, day_of_week
            )
            print(f"New entry added: '{description}' with category '{category}'.")

        # Append the new data to the CSV file instead of rewriting it entirely
        self._append_to_csv(
            date, tokenized_description, amount, category, day_of_month, day_of_week
        )

        self._create_and_fit_model()

    def _append_to_csv(
        self,
        date: date,
        description: str,
        amount: float,
        category: str,
        day_of_month: int,
        day_of_week: int,
    ) -> None:
        """Append the new entry to the CSV file without overwriting the whole file.

        Ensures a newline is present before appending the new entry.
        """
        new_data = pd.DataFrame(
            {
                "date": [date],
                "desc": [description],
                "amount": [amount],
                "cat": [category],
            }
        )

        # Check if the file already exists
        file_exists = os.path.isfile(self.data_file)

        # Ensure there's a newline at the end of the file before appending new data
        if file_exists:
            with open(self.data_file, "rb+") as f:
                f.seek(-1, os.SEEK_END)  # Move to the last byte
                last_char = f.read(1)
                if last_char != b"\n":  # Check if the last character is a newline
                    f.write(b"\n")  # If not, add a newline

        # Now append the new data
        new_data.to_csv(self.data_file, mode="a", header=False, index=False)

    def _handle_existing_entry_conflict(
        self,
        description: str,
        existing_category: str,
        date: date,
        amount: float,
        new_category: str,
        day_of_month: int,
        day_of_week: int,
    ):
        """Handle the case where an entry with the same description exists but has a different category.

        Allows the user to choose between updating, adding a new entry, or skipping.
        """
        print(
            f"Description '{description}' already exists with category '{existing_category}'."
        )
        action = input(
            "Choose action:\n"
            "1. Update existing entry\n"
            "2. Add new entry\n"
            "3. Skip update\n"
            "Enter choice (1/2/3): "
        )

        if action == "1":
            # Update the existing entry with the new category
            self.training_data.loc[self.training_data["desc"] == description, "cat"] = (
                new_category
            )
            print(
                f"Existing entry for '{description}' updated to category '{new_category}'."
            )
        elif action == "2":
            # Add a new entry despite the conflict
            self._add_new_entry(
                date, description, amount, new_category, day_of_month, day_of_week
            )
            print(
                f"New entry added for '{description}' with category '{new_category}'."
            )
        else:
            # Skip the update process
            print("Update skipped.")

    def _add_new_entry(
        self,
        date: date,
        description: str,
        amount: float,
        category: str,
        day_of_month: int,
        day_of_week: int,
    ):
        """Add a new entry to the training data."""
        new_data = pd.DataFrame(
            {
                "date": [date],
                "desc": [description],
                "amount": [amount],
                "cat": [category],
                "day_of_month": [day_of_month],
                "day_of_week": [day_of_week],
            }
        )
        self.training_data = pd.concat(
            [self.training_data, new_data], ignore_index=True
        )

    def _tokenize_description(self, description: str) -> str:
        """Tokenize the description using CountVectorizer."""
        vectorizer = CountVectorizer(analyzer=str.split)
        tokens = vectorizer.build_analyzer()(description)
        return " ".join(tokens)
