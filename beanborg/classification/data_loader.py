"""Data loading and manipulation module for transaction training data.

This module provides functionality for loading, processing, and updating
transaction training data stored in CSV format.
"""

from pathlib import Path
from typing import Any, Dict, Union

import pandas as pd
from pandas import DataFrame, Series


class DataLoadError(Exception):
    """Raised when data loading operations fail."""
    pass


class DataLoader:
    """Handles loading and manipulation of transaction training data.

    This class provides static methods for loading CSV data files,
    processing dates, and adding new training examples.
    """

    REQUIRED_COLUMNS = ['date', 'desc', 'amount', 'cat']
    DATE_FORMAT = "%Y-%m-%d"

    @staticmethod
    def load_data(filepath: Union[str, Path]) -> DataFrame:
        """Load and process transaction training data from CSV.

        Creates the file with header if it doesn't exist, then loads
        the data and adds derived date features.

        Args:
            filepath: Path to the CSV file

        Returns:
            DataFrame with processed transaction data

        Raises:
            DataLoadError: If file operations or data processing fails
        """
        try:
            filepath = Path(filepath).expanduser()

            # Create file if it doesn't exist
            if not filepath.exists():
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(",".join(DataLoader.REQUIRED_COLUMNS) + "\n")

            # Load and process data
            data = pd.read_csv(filepath)

            # Validate columns
            missing_cols = set(DataLoader.REQUIRED_COLUMNS) - set(data.columns)
            if missing_cols:
                raise DataLoadError(
                    f"Missing required columns: {', '.join(missing_cols)}"
                )

            # Process dates and add derived features
            try:
                data["date"] = pd.to_datetime(
                    data["date"],
                    format=DataLoader.DATE_FORMAT
                )
                data["day_of_month"] = data["date"].dt.day
                data["day_of_week"] = data["date"].dt.dayofweek
            except ValueError as e:
                raise DataLoadError(f"Error processing dates: {e}") from e

            # Ensure description is string type
            data["desc"] = data["desc"].astype(str)

            return data

        except Exception as e:
            if not isinstance(e, DataLoadError):
                raise DataLoadError(f"Error loading data: {e}") from e
            raise

    @staticmethod
    def add_training_row(
        filepath: Union[str, Path],
        row: Union[Series, Dict[str, Any]]
    ) -> None:
        """Add a new row to the training data.

        Args:
            filepath: Path to the CSV file
            row: New data row (pandas Series or dictionary)

        Raises:
            DataLoadError: If file operations fail
            ValueError: If row data is invalid
        """
        try:
            filepath = Path(filepath).expanduser()

            # Validate row data
            if isinstance(row, dict):
                row = Series(row)

            missing_cols = set(DataLoader.REQUIRED_COLUMNS) - set(row.index)
            if missing_cols:
                raise ValueError(
                    f"Missing required columns in row: {', '.join(missing_cols)}"
                )

            # Load existing data and append new row
            if filepath.exists():
                data = pd.read_csv(filepath)
                data = pd.concat([data, row.to_frame().T], ignore_index=True)
                data.to_csv(filepath, index=False)
            else:
                raise DataLoadError(f"Training data file not found: {filepath}")

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise DataLoadError(f"Error adding training row: {e}") from e

    @staticmethod
    def _validate_data(data: DataFrame) -> None:
        """Validate the structure and content of training data.

        Args:
            data: DataFrame to validate

        Raises:
            ValueError: If data validation fails
        """
        # Validate columns
        missing_cols = set(DataLoader.REQUIRED_COLUMNS) - set(data.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Validate date format
        if not pd.api.types.is_datetime64_any_dtype(data["date"]):
            raise ValueError("Date column must be datetime type")

        # Validate non-null values
        null_counts = data[DataLoader.REQUIRED_COLUMNS].isnull().sum()
        if null_counts.any():
            null_cols = null_counts[null_counts > 0].index.tolist()
            raise ValueError(f"Null values found in columns: {', '.join(null_cols)}")
