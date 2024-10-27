"""Configuration handling for transaction processing application.

This module provides classes for managing configuration settings related to
transaction processing, including CSV file handling, data indexing, and
processing rules.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from yaml.loader import FullLoader


@dataclass
class Rules:
    """Configuration for transaction processing rules.

    Attributes:
        bc_file: Path to Beancount file
        rules_folder: Directory containing rule definitions
        account: Default account for transactions
        currency: Default currency for transactions
        default_expense: Default expense category
        force_negative: Whether to force negative amounts
        invert_negative: Whether to invert negative amounts
        origin_account: Source account for transactions
        ruleset: List of processing rules to apply
        advanced_duplicate_detection: Whether to use advanced duplicate detection
        training_data: Path to training data file
        use_llm: Whether to use language model for classification
    """
    bc_file: Optional[str] = None
    rules_folder: Optional[str] = None
    account: Optional[str] = None
    currency: Optional[str] = None
    default_expense: Optional[str] = None
    force_negative: Optional[bool] = None
    invert_negative: Optional[bool] = None
    origin_account: Optional[str] = None
    ruleset: List[Dict[str, Any]] = None
    advanced_duplicate_detection: Optional[bool] = None
    training_data: Optional[str] = None
    use_llm: Optional[bool] = None

    def __post_init__(self) -> None:
        """Set default values for optional fields."""
        self.ruleset = self.ruleset or []


@dataclass
class Indexes:
    """Configuration for CSV file column indexes.

    Attributes:
        date: Index of date column
        counterparty: Index of counterparty column
        amount: Index of amount column
        account: Index of account column
        currency: Index of currency column
        tx_type: Index of transaction type column
        amount_in: Index of incoming amount column
        narration: Index of narration column
    """
    date: Optional[int] = None
    counterparty: Optional[int] = None
    amount: Optional[int] = None
    account: Optional[int] = None
    currency: Optional[int] = None
    tx_type: Optional[int] = None
    amount_in: Optional[int] = None
    narration: Optional[int] = None


@dataclass
class Csv:
    """Configuration for CSV file handling.

    Attributes:
        download_path: Path to download CSV files
        name: Base name for CSV files
        ref: Bank reference identifier
        separator: CSV field separator
        date_format: Format string for dates
        skip: Number of header rows to skip
        target: Target directory for processed files
        archive: Archive directory for processed files
        post_script_path: Path to post-processing script
        keep_original: Whether to keep original files
    """
    download_path: str
    name: str
    ref: str
    separator: Optional[str] = None
    date_format: Optional[str] = None
    skip: Optional[int] = None
    target: Optional[str] = None
    archive: Optional[str] = None
    post_script_path: Optional[str] = None
    keep_original: Optional[bool] = None


@dataclass
class Config:
    """Main configuration container.

    This class holds all configuration settings and provides methods
    for loading configuration from YAML files.

    Attributes:
        csv: CSV file configuration
        indexes: Column index configuration
        rules: Processing rules configuration
        debug: Debug mode flag
    """
    csv: Csv
    indexes: Indexes
    rules: Rules
    debug: bool = False

    @staticmethod
    def load(loader: yaml.Loader, node: yaml.Node) -> 'Config':
        """Load configuration from YAML node.

        Args:
            loader: YAML loader instance
            node: YAML node containing configuration

        Returns:
            Configured Config instance

        Raises:
            ValueError: If required configuration is missing
        """
        values = loader.construct_mapping(node, deep=True)

        # Validate required sections
        if 'csv' not in values:
            raise ValueError("Missing required 'csv' section in configuration")

        csv_data = values["csv"]
        csv = Csv(
            download_path=csv_data["download_path"],
            name=csv_data["name"],
            ref=csv_data["bank_ref"],
            separator=csv_data.get("separator", ","),
            date_format=csv_data["date_format"],
            skip=csv_data.get("skip", 1),
            target=csv_data.get("target", "tmp"),
            archive=csv_data.get("archive_path", "archive"),
            post_script_path=csv_data.get("post_move_script"),
            keep_original=csv_data.get("keep_original", False)
        )

        idx = values.get("indexes", {})
        indexes = Indexes(
            date=idx.get("date", 0),
            counterparty=idx.get("counterparty", 3),
            amount=idx.get("amount", 4),
            account=idx.get("account", 1),
            currency=idx.get("currency", 5),
            tx_type=idx.get("tx_type", 2),
            amount_in=idx.get("amount_in"),
            narration=idx.get("narration")
        )

        rls = values.get("rules", {})
        rules = Rules(
            bc_file=rls.get("beancount_file", "main.ldg"),
            rules_folder=rls.get("rules_folder", "rules"),
            account=rls.get("account"),
            currency=rls.get("currency"),
            default_expense=rls.get("default_expense", "Expenses:Unknown"),
            force_negative=rls.get("force_negative", False),
            invert_negative=rls.get("invert_negative", False),
            origin_account=rls.get("origin_account"),
            ruleset=rls.get("ruleset", []),
            advanced_duplicate_detection=rls.get("advanced_duplicate_detection", True),
            training_data=rls.get("training_data", "training_data.csv"),
            use_llm=rls.get("use_llm", False)
        )

        return Config(csv, indexes, rules)


def init_config(config_path: Union[str, Path], debug: bool = False) -> Config:
    """Initialize configuration from a YAML file.

    Args:
        config_path: Path to configuration file
        debug: Enable debug mode

    Returns:
        Configured Config instance

    Raises:
        FileNotFoundError: If configuration file doesn't exist
        yaml.YAMLError: If configuration file is malformed
    """
    yaml.add_constructor("!Config", Config.load)

    config_path = Path(config_path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as file:
            config = yaml.load(file, Loader=FullLoader)
    except yaml.scanner.ScannerError as e:
        raise yaml.YAMLError(f"Malformed configuration file: {config_path}") from e

    config.debug = debug
    return config
