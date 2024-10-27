# -*- coding: utf-8 -*-
"""Decision table handling for transaction processing.

This module provides functionality for loading and processing decision tables
from CSV files. Decision tables are used to map transaction data based on
various string matching rules.
"""

import csv
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Iterator, Tuple, Union


class MatchType(Enum):
    """Supported string matching types."""

    EQUALS = "equals"
    EQUALS_IC = "equals_ic"
    STARTS_WITH = "startsWith"
    ENDS_WITH = "endsWith"
    CONTAINS = "contains"
    CONTAINS_IC = "contains_ic"
    EQ = "eq"  # Alias for EQUALS
    SW = "sw"  # Alias for STARTS_WITH
    EW = "ew"  # Alias for ENDS_WITH
    CO = "co"  # Alias for CONTAINS


class DecisionTableError(Exception):
    """Base exception for decision table errors."""

    pass


class InvalidRuleError(DecisionTableError):
    """Raised when a rule in the decision table is invalid."""

    pass


class StringMatcher:
    """Provides string matching operations for decision tables."""

    @staticmethod
    def equals(string_a: str, string_b: str) -> bool:
        """Exact string equality comparison."""
        return string_a == string_b

    @staticmethod
    def equals_ignore_case(string_a: str, string_b: str) -> bool:
        """Case-insensitive string equality comparison."""
        return string_a.casefold() == string_b.casefold()

    @staticmethod
    def starts_with(string_a: str, string_b: str) -> bool:
        """Check if string_a starts with string_b."""
        return string_a.startswith(string_b)

    @staticmethod
    def ends_with(string_a: str, string_b: str) -> bool:
        """Check if string_a ends with string_b."""
        return string_a.endswith(string_b)

    @staticmethod
    def contains(string_a: str, string_b: str) -> bool:
        """Check if string_a contains string_b."""
        return string_b in string_a

    @staticmethod
    def contains_ignore_case(string_a: str, string_b: str) -> bool:
        """Case-insensitive containment check."""
        return string_b.casefold() in string_a.casefold()


class DecisionTable:
    """Handles loading and processing of decision tables."""

    def __init__(self):
        """Initialize the decision table matcher."""
        self._matchers: Dict[str, Callable[[str, str], bool]] = {
            MatchType.EQUALS.value: StringMatcher.equals,
            MatchType.EQUALS_IC.value: StringMatcher.equals_ignore_case,
            MatchType.STARTS_WITH.value: StringMatcher.starts_with,
            MatchType.ENDS_WITH.value: StringMatcher.ends_with,
            MatchType.CONTAINS.value: StringMatcher.contains,
            MatchType.CONTAINS_IC.value: StringMatcher.contains_ignore_case,
            MatchType.EQ.value: StringMatcher.equals,
            MatchType.SW.value: StringMatcher.starts_with,
            MatchType.EW.value: StringMatcher.ends_with,
            MatchType.CO.value: StringMatcher.contains,
        }

    def init_table(
        self, file_path: Union[str, Path], debug: bool = False
    ) -> Dict[str, Tuple[str, str]]:
        """Load and initialize a decision table from a CSV file.

        Args:
            file_path: Path to the decision table CSV file
            debug: Enable debug output

        Returns:
            Dictionary mapping patterns to (match_type, result) tuples

        Raises:
            DecisionTableError: If the file is invalid or cannot be processed
        """
        table = {}
        file_path = Path(file_path)
        full_path = Path.cwd() / file_path

        if not full_path.is_file() or full_path.stat().st_size == 0:
            if debug:
                print(f"The decision table file: {file_path} is missing or empty.")
            return table

        try:
            with open(full_path) as csv_file:
                csv_reader = csv.reader(self._decomment(csv_file), delimiter=";")
                next(csv_reader)  # skip header row

                for row in csv_reader:
                    if any(row):  # Skip empty rows
                        if len(row) == 3:
                            table[row[0]] = (row[1], row[2])
                        else:
                            raise InvalidRuleError(f"Invalid rule: {', '.join(row)}")
        except Exception as e:
            raise DecisionTableError(f"Error processing decision table: {e}") from e

        return table

    @staticmethod
    def _decomment(csvfile: Iterator[str]) -> Iterator[str]:
        """Remove comments from CSV file.

        Args:
            csvfile: CSV file iterator

        Yields:
            Rows with comments removed
        """
        for row in csvfile:
            raw = row.split("#")[0].strip()
            if raw:
                yield row

    def resolve(
        self, table: Dict[str, Tuple[str, str]], string: str, default: str
    ) -> str:
        """Resolve a string using the decision table.

        Args:
            table: Decision table dictionary
            string: String to resolve
            default: Default value if no match is found

        Returns:
            Resolved string or default value

        Raises:
            DecisionTableError: If an invalid match type is encountered
        """
        for pattern, (match_type, result) in table.items():
            matcher = self._matchers.get(match_type)
            if matcher is None:
                raise DecisionTableError(f"Invalid match type: {match_type}")

            try:
                if matcher(string, pattern):
                    return result
            except Exception as e:
                raise DecisionTableError(
                    f"Error matching pattern '{pattern}': {e}"
                ) from e

        return default


# Module-level interface for backward compatibility
_decision_table = DecisionTable()


def init_decision_table(
    file: Union[str, Path], debug: bool = False
) -> Dict[str, Tuple[str, str]]:
    """Initialize a decision table from a file."""
    return _decision_table.init_table(file, debug)


def resolve_from_decision_table(
    table: Dict[str, Tuple[str, str]], string: str, default: str
) -> str:
    """Resolve a string using a decision table."""
    return _decision_table.resolve(table, string, default)
