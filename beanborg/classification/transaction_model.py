import pandas as pd
import numpy as np
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import make_pipeline
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import KNeighborsClassifier
import os

class TransactionModel:
    def __init__(self, training_data, data_file):
        self.training_data = training_data
        self.data_file = data_file
        self._create_and_fit_model()

    def _remove_single_sample_classes(self, X, y):
        class_counts = y.value_counts()
        classes_to_keep = class_counts[class_counts >= 2].index
        mask = y.isin(classes_to_keep)
        return X[mask], y[mask]

    def _create_and_fit_model(self):
        X = self.training_data[["desc", "day_of_month", "day_of_week"]]
        y = self.training_data["cat"]

        # Remove classes with only one sample
        X, y = self._remove_single_sample_classes(X, y)

        # Encode target labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)

        # Create feature processing pipeline
        feature_pipeline = ColumnTransformer([
            ('text', make_pipeline(
                CountVectorizer(analyzer=str.split),  # Removed token_pattern
                StandardScaler(with_mean=False)
            ), 'desc'),
            ('num', StandardScaler(), ['day_of_month', 'day_of_week'])
        ])

        # Create KNN classifier
        n_neighbors = min(5, len(y) - 1)
        knn = KNeighborsClassifier(n_neighbors=n_neighbors)

        # Create pipeline with SMOTE
        self.model = ImbPipeline([
            ('features', feature_pipeline),
            ('smote', SMOTE(k_neighbors=min(5, min(y.value_counts()) - 1))),
            ('classifier', knn)
        ])

        # Fit the model
        self.model.fit(X, y_encoded)

    def predict(self, text, day_of_month, day_of_week, n=3):
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

    def update_training_data(self, date, description, amount, category, day_of_month, day_of_week):
        """
        Updates the training data with a new or existing entry and retrains the model.
        """
        # Check if the description already exists
        existing_entry = self.training_data[self.training_data['desc'] == description]

        if not existing_entry.empty:
            existing_category = existing_entry['cat'].iloc[0]

            if existing_category != category:
                # Conflict found: Ask user how to handle the conflicting category
                self._handle_existing_entry_conflict(description, existing_category, date, amount, category, day_of_month, day_of_week)
            else:
                # Entry already exists with the same category, no update needed
                print(f"Entry already exists with category '{existing_category}'. Skipping update.")
                return
        else:
            # Add a new entry
            self._add_new_entry(date, description, amount, category, day_of_month, day_of_week)
            print(f"New entry added: '{description}' with category '{category}'.")

        # Append the new data to the CSV file instead of rewriting it entirely
        self._append_to_csv(date, description, amount, category, day_of_month, day_of_week)


        self._create_and_fit_model()

    def _append_to_csv(self, date, description, amount, category, day_of_month, day_of_week):
        """
        Append the new entry to the CSV file without overwriting the whole file.
        Ensures a newline is present before appending the new entry.
        """
        new_data = pd.DataFrame({
            'date': [date],
            'desc': [description],
            'amount': [amount],
            'cat': [category],
            'day_of_month': [day_of_month],
            'day_of_week': [day_of_week]
        })

        # Check if the file already exists
        file_exists = os.path.isfile(self.data_file)

        # Ensure there's a newline at the end of the file before appending new data
        if file_exists:
            with open(self.data_file, 'rb+') as f:
                f.seek(-1, os.SEEK_END)  # Move to the last byte
                last_char = f.read(1)
                if last_char != b'\n':  # Check if the last character is a newline
                    f.write(b'\n')  # If not, add a newline

        # Now append the new data
        new_data.to_csv(self.data_file, mode='a', header=not file_exists, index=False)

    def _handle_existing_entry_conflict(self, description, existing_category, date, amount, new_category, day_of_month, day_of_week):
        """
        Handle the case where an entry with the same description exists but has a different category.
        Allows the user to choose between updating, adding a new entry, or skipping.
        """
        print(f"Description '{description}' already exists with category '{existing_category}'.")
        action = input(
            "Choose action:\n"
            "1. Update existing entry\n"
            "2. Add new entry\n"
            "3. Skip update\n"
            "Enter choice (1/2/3): "
        )

        if action == '1':
            # Update the existing entry with the new category
            self.training_data.loc[self.training_data['desc'] == description, 'cat'] = new_category
            print(f"Existing entry for '{description}' updated to category '{new_category}'.")
        elif action == '2':
            # Add a new entry despite the conflict
            self._add_new_entry(date, description, amount, new_category, day_of_month, day_of_week)
            print(f"New entry added for '{description}' with category '{new_category}'.")
        else:
            # Skip the update process
            print("Update skipped.")

    def _add_new_entry(self, date, description, amount, category, day_of_month, day_of_week):
        """
        Add a new entry to the training data.
        """
        new_data = pd.DataFrame({
            'date': [date],
            'desc': [description],
            'amount': [amount],
            'cat': [category],
            'day_of_month': [day_of_month],
            'day_of_week': [day_of_week]
        })
        self.training_data = pd.concat([self.training_data, new_data], ignore_index=True)
