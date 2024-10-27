# -*- coding: utf-8 -*-
"""Rule engine module for transaction processing.

This module provides functionality for loading, managing, and executing rules
on financial transactions. It supports both built-in and custom rules, and
handles rule initialization and execution in a sequential manner.
"""

import fnmatch
import logging
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type

from beancount.core.data import Posting, Transaction

from .Context import Context
from .rules import (
    IgnoreByContainsStringAtPos,
    IgnoreByPayee,
    IgnoreByStringAtPos,
    ReplaceAsset,
    ReplaceExpense,
    ReplacePayee,
    Rule,
    SetAccounts,
)

# Configure logging
logger = logging.getLogger(__name__)

# Constants
RULE_FILE_PATTERN: str = "*.py"
DEFAULT_RULES: List[str] = ["ReplaceAsset"]


@dataclass
class RuleDef:
    """Definition of a rule and its attributes.

    Attributes:
        rule: The rule class or function to be executed
        attributes: Dictionary of rule properties and their values
    """

    rule: Any  # Type hint could be more specific based on rule structure
    attributes: Optional[Dict[str, List[str]]]

    def get(self, key: str) -> List[str]:
        """Get rule attributes by key.

        Args:
            key: Attribute key to lookup

        Returns:
            List of attribute values

        Raises:
            KeyError: If key doesn't exist in attributes
        """
        if self.attributes is None:
            return []
        return self.attributes[key]


class RuleInit(Rule):
    """Initialization rule that creates a basic transaction structure."""

    def __init__(self, name: str, context: Context):
        """Initialize the rule.

        Args:
            name: Name of the rule
            context: Context object containing configuration
        """
        super().__init__(name, context)

    def execute(
        self, csv_line: Dict[str, str], transaction: Optional[Transaction] = None
    ) -> Tuple[bool, Transaction]:
        """Create an empty transaction structure.

        Args:
            csv_line: CSV line data (unused in this rule)
            transaction: Optional existing transaction (unused in this rule)

        Returns:
            Tuple of (False, empty Transaction)
        """
        empty_posting = Posting(
            account=None,
            units=None,
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )

        return (
            False,
            Transaction(
                meta=None,
                date=None,
                flag="*",
                payee=None,
                narration=None,
                tags=None,
                links=None,
                postings=[empty_posting, empty_posting],
            ),
        )


@dataclass
class RuleErrorContext:
    """Context information for rule errors."""

    rule_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class RuleEngineError(Exception):
    """Base exception for rule engine errors."""

    def __init__(self, message: str, context: Optional[RuleErrorContext] = None):
        """Initialize the exception."""
        self.context = context or RuleErrorContext()
        super().__init__(message)


class RuleLoadError(RuleEngineError):
    """Exception raised when rule loading fails."""

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        context_info = []
        if self.context.rule_name:
            context_info.append(f"rule='{self.context.rule_name}'")
        if self.context.file_path:
            context_info.append(f"file='{self.context.file_path}'")
        if self.context.line_number:
            context_info.append(f"line={self.context.line_number}")

        context_str = f" ({', '.join(context_info)})" if context_info else ""
        return f"{super().__str__()}{context_str}"


class RuleEngine:
    """Engine for loading and executing transaction processing rules.

    This class manages the loading of both built-in and custom rules,
    and provides methods to execute these rules on transaction data.
    """

    # Define known rules mapping
    BUILT_IN_RULES = {
        "ReplaceAsset": ReplaceAsset,
        "ReplaceExpense": ReplaceExpense,
        "ReplacePayee": ReplacePayee,
        "IgnoreByPayee": IgnoreByPayee,
        "IgnoreByStringAtPos": IgnoreByStringAtPos,
        "IgnoreByContainsStringAtPos": IgnoreByContainsStringAtPos,
        "SetAccounts": SetAccounts,
    }

    def __init__(self, ctx: Context):
        """Initialize the rule engine.

        Args:
            ctx: Context object containing configuration

        Raises:
            Warning: If no rules file is specified
        """
        self._ctx = ctx
        self.rules: Dict[str, RuleDef] = {}

        self._load_rules()
        self._add_default_rules()

    def _load_rules(self) -> None:
        """Load rules from configuration and custom rules directory."""
        logger.debug("Loading rules from configuration")
        try:
            custom_rules = self._load_custom_rules()

            if not self._ctx.ruleset:
                print("\u26A0 No rules file specified for this financial institution")
                return

            for rule_config in self._ctx.ruleset:
                rule_name = rule_config.get("name")
                if not rule_name:
                    logger.warning("Skipping rule with no name in configuration")
                    continue
                logger.debug("Processing rule configuration: %s", rule_name)
                rule_props = {
                    key: value for key, value in rule_config.items() if key != "name"
                }
                try:
                    if rule_name in custom_rules:
                        logger.debug("Loading custom rule: %s", rule_name)
                        self.rules[rule_name] = RuleDef(
                            custom_rules[rule_name], rule_props
                        )
                    elif rule_name in self.BUILT_IN_RULES:
                        # Load from built-in rules
                        logger.debug("Loading built-in rule: %s", rule_name)
                        unique_name = f"{rule_name}|{uuid.uuid4().hex.upper()[:6]}"
                        self.rules[unique_name] = RuleDef(
                            self.BUILT_IN_RULES[rule_name], rule_props
                        )
                    else:
                        logger.error("Unknown rule: %s", rule_name)
                        raise RuleLoadError(f"Unknown rule type: {rule_name}")
                except Exception as e:
                    raise RuleLoadError(f"Failed to load rule '{rule_name}'") from e
        except Exception as e:
            if not isinstance(e, RuleLoadError):
                raise RuleLoadError("Failed to load rules") from e
            raise

    def _add_default_rules(self) -> None:
        """Add default rules if not already present."""
        if self._ctx.rules_dir and not self._has_rule("ReplaceAsset"):
            self.rules["ReplaceAsset"] = RuleDef(ReplaceAsset, None)

    def _has_rule(self, name: str) -> bool:
        """Check if a rule with the given name exists.

        Args:
            name: Name of the rule to check

        Returns:
            bool: True if rule exists, False otherwise
        """
        return any(rule_name.startswith(name) for rule_name in self.rules)

    def _load_custom_rules(self) -> Dict[str, Type[Rule]]:
        """Load custom rules from the rules directory.

        Returns:
            Dictionary mapping rule names to rule classes

        Raises:
            ImportError: If custom rule module cannot be imported
        """
        custom_rules: Dict[str, Type[Rule]] = {}

        if not self._ctx.rules_dir:
            return custom_rules

        rules_path = os.path.join(os.getcwd(), self._ctx.rules_dir)
        if not os.path.isdir(rules_path):
            if self._ctx.debug:
                print("Custom rules folder not found...ignoring")
            return custom_rules

        sys.path.append(rules_path)

        try:
            for rule_file in fnmatch.filter(os.listdir(rules_path), RULE_FILE_PATTERN):
                module_name = rule_file[:-3]
                module = __import__(module_name, globals={})
                rule_class = getattr(module, module_name)

                # TODO: Add validation that rule_class inherits from Rule
                custom_rules[module_name] = rule_class

        except (ImportError, AttributeError) as e:
            if self._ctx.debug:
                print(f"Error loading custom rule: {e}")

        return custom_rules

    def execute(self, csv_line: Dict[str, str]) -> Transaction:
        """Execute all rules on a CSV line.

        Args:
            csv_line: Dictionary containing CSV line data

        Returns:
            Processed Transaction object

        Raises:
            Exception: If rule execution fails
        """
        final, transaction = RuleInit("init", self._ctx).execute(csv_line)

        for rule_name, rule_def in self.rules.items():
            if not final:
                if self._ctx.debug:
                    print(f"Executing rule: {rule_def.rule}")
                try:
                    rule = rule_def.rule(rule_name, self._ctx)
                    final, transaction = rule.execute(csv_line, transaction, rule_def)
                except Exception as e:
                    if self._ctx.debug:
                        print(f"Error executing rule {rule_name}: {e}")
                    raise

        return transaction
