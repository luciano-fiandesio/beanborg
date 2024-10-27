# -*- coding: utf-8 -*-
"""Rule definitions for transaction processing.

This module provides a collection of rules for processing financial transactions.
Each rule implements specific logic for modifying or filtering transactions based
on configured criteria.
"""

import abc
import fnmatch
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional

from beancount.core.data import Posting, Transaction

from .Context import Context
from .decision_tables import init_decision_table, resolve_from_decision_table


@dataclass
class RuleResult:
    """Result of a rule execution.

    Attributes:
        final: Whether this is the final rule to execute
        transaction: The resulting transaction or None if ignored
    """

    final: bool
    transaction: Optional[Transaction]


class LookUpCache:
    """Simple cache for lookup tables."""

    _cache: Dict[str, Any] = {}

    @staticmethod
    def init_decision_table(key, path):
        """Initialize a decision table and cache it."""
        if key in LookUpCache._cache:
            return LookUpCache._cache[key]

        data = init_decision_table(path)
        LookUpCache._cache[key] = data
        return data


class Rule(abc.ABC):
    """Abstract base class for rules."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, name: str, context: Context):
        """Initialize the rule.

        Args:
            name: Name of the rule
            context: Context object containing configuration
        """
        self.name = name
        self.context = context

    @abc.abstractmethod
    def execute(
        self,
        csv_line: Dict[str, str],
        transaction: Optional[Transaction] = None,
        rule_def: Optional[Dict[str, Any]] = None,
    ) -> RuleResult:
        """Execute the rule on a transaction.

        Args:
            csv_line: CSV data for the transaction
            transaction: Current transaction state
            rule_def: Rule configuration

        Returns:
            RuleResult containing processing result
        """
        pass

    def check_account_from_to(self, rule_def: Dict[str, Any]) -> None:
        """Check if the rule has from and to accounts.

        Args:
            rule_def: Rule definition

        Raises:
            Exception: If from or to accounts are missing
        """
        if rule_def.get("from") is None or rule_def.get("to") is None:
            raise Exception(
                "Account from and to required for rule: {rule}".format(
                    rule=rule_def.rule.__name__
                )
            )

    def fail_if_attribute_missing(
        self, rule_def: Dict[str, Any], attribute_name: str
    ) -> None:
        """Fail if an attribute is missing."""
        if rule_def.get(attribute_name) is None:
            raise Exception(
                "Attribute {attribute_name} required for rule: {rule} ".format(
                    attribute_name=attribute_name, rule=rule_def.rule.__name__
                )
            )


class SetAccounts(Rule):
    """Assign a from/to asset or account to a transaction, depending on the value of a given cvs index.

    Rule attributes:
        name: rule name (Set_Accounts)
        from: asset or account
        to:   asset or account
        csv_index: csv row index to analyze (base-0)
        csv_values: semicolon delimited list of strings.
                    If any of the values matches the
                    value at the csv row's index, the from/to values
                    are assigned.
                    The string evaluation is case insensitive.

    Example:
        -  name: Set_Accounts
           from: Assets:Bank1:Bob:Savings
           to: Account:Groceries
           csv_index: 4
           csv_values: superfood;super_food;

    """

    def execute(
        self,
        csv_line: Dict[str, str],
        transaction: Transaction,
        rule_def: Dict[str, Any],
    ) -> RuleResult:
        """Execute the rule.

        Args:
            csv_line: CSV line data
            transaction: Transaction object
            rule_def: Rule definition
        """
        # current value at index for the current row
        # csv_field_val = csv_line[ruleDef.csv_index].lower()
        csv_field_val = csv_line[rule_def.get("csv_index")].lower().strip()

        # values specified in the rule definition
        vals = rule_def.get("csv_values").split(";")

        match = False
        for val in vals:
            # Use fnmatch to allow wildcard matching
            if fnmatch.fnmatch(csv_field_val, val.lower().strip()):
                match = True
                break

        if match:
            new_posting = [
                Posting(
                    account=rule_def.get("from"),
                    units=None,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                Posting(
                    account=rule_def.get("to"),
                    units=None,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]

            return (True, transaction._replace(postings=new_posting))

        return (False, transaction)


class ReplacePayee(Rule):
    """Replaces the name of the transaction counterparty.

    (for instance: McDonald -> Mc Donald Restaurant)
    The rule file containing the substitution rules
    must be located in the rules folder and must be named "payee.rules"
    """

    def execute(
        self,
        csv_line: Dict[str, str],
        transaction: Transaction,
        rule_def: Dict[str, Any],
    ) -> RuleResult:
        """Execute the rule.

        Args:
            csv_line: CSV line data
            transaction: Transaction object
            rule_def: Rule definition
        """
        table = os.path.join(self.context.rules_dir, "payee.rules")
        if not os.path.isfile(table):
            print(
                "file: %s does not exist! - The 'ReplacePayee' rules \
                    requires the payee.rules file."
                % (table)
            )
            sys.exit(-1)

        return (
            False,
            transaction._replace(
                payee=resolve_from_decision_table(
                    LookUpCache.init_decision_table("payee", table),
                    csv_line[self.context.payee_pos],
                    csv_line[self.context.payee_pos],
                )
            ),
        )


class ReplaceAsset(Rule):
    """Assigns an account to a transaction, based on value of the 'account' index of a CSV file row.

    This rule is useful to assign the correct source account
    of a CSV transaction.

    The rule is based on the 'asset.rules' look-up file.
    If no 'asset.rules' file is found, the account
    will be resolved to "Assets:Unknown" or
    to the value of the property `rules.origin_account` of the config file.
    """

    def execute(
        self,
        csv_line: Dict[str, str],
        transaction: Transaction,
        rule_def: Dict[str, Any],
    ) -> RuleResult:
        """Execute the rule."""
        asset = None
        table = os.path.join(self.context.rules_dir, "asset.rules")
        if self.context.force_account:
            asset = self.context.force_account
        else:
            if not os.path.isfile(table):
                print(
                    "file: %s does not exist! - \
                        The 'ReplaceAsset' rules requires the asset.rules \
                            file."
                    % (table)
                )
                sys.exit(-1)

            asset = resolve_from_decision_table(
                LookUpCache.init_decision_table("asset", table),
                (
                    self.context.account
                    if self.context.account is not None
                    else csv_line[self.context.account_pos]
                ),
                "Assets:Unknown",
            )

        if asset:
            posting = Posting(asset, None, None, None, None, None)
            new_postings = [posting] + [transaction.postings[1]]
            return (False, transaction._replace(postings=new_postings))

        return (False, transaction)


class ReplaceExpense(Rule):
    """Categorizes a transaction.

    A transaction is categorized by assigning the account
    extracted from a look-up table
    based on the 'payee_pos' index of a CSV file row.

    The rule is based on the 'payee.rules' look-up file.
    """

    def execute(
        self,
        csv_line: Dict[str, str],
        transaction: Transaction,
        rule_def: Dict[str, Any],
    ) -> RuleResult:
        """Execute the rule."""
        table = os.path.join(self.context.rules_dir, "account.rules")

        if not os.path.isfile(table):
            print(
                "file: % s does not exist! - The 'ReplaceExpense' rules \
                  requires the account.rules file."
                % (table)
            )
            sys.exit(-1)

        expense = resolve_from_decision_table(
            LookUpCache.init_decision_table("account", table),
            csv_line[self.context.payee_pos],
            self.context.default_expense,
        )
        if expense:
            posting = Posting(expense, None, None, None, None, None)
            new_postings = [transaction.postings[0]] + [posting]
            return (False, transaction._replace(postings=new_postings))

        return (False, transaction)


class IgnoreByPayee(Rule):
    """Ignores a transaction based on the value of the payee index."""

    def execute(
        self,
        csv_line: Dict[str, str],
        transaction: Transaction,
        rule_def: Dict[str, Any],
    ) -> RuleResult:
        """Execute the rule."""
        self.fail_if_attribute_missing(rule_def, "ignore_payee")
        for ignorable_payee in rule_def.get("ignore_payee"):
            if ignorable_payee.lower() in csv_line[self.context.payee_pos].lower():
                return (True, None)

        return (False, transaction)


class IgnoreByStringAtPos(Rule):
    """Ignores a transaction based on the value of the specified index.

    For instance, given this csv entry:

    10.12.2022,bp-fuel,20US$

    and this rule:

    -  name: Ignore_By_ContainsStringAtPos
           ignore_string_at_pos:
               - bp-fuel;1

    The row will be ignored, because the string "bp-fuel" matches
    the index at position 1.

    Example:
        -  name: Ignore_By_StringAtPos
           ignore_string_at_pos:
               - val;3
    """

    def execute(
        self,
        csv_line: Dict[str, str],
        transaction: Transaction,
        rule_def: Dict[str, Any],
    ) -> RuleResult:
        """Execute the rule."""
        self.fail_if_attribute_missing(rule_def, "ignore_string_at_pos")
        for ignorable in rule_def.get("ignore_string_at_pos"):
            pos = int(ignorable.split(";")[1])
            str_to_ignore = ignorable.split(";")[0]

            if str_to_ignore.lower().strip() == csv_line[pos].lower().strip():
                return (True, None)

        return (False, transaction)


class IgnoreByContainsStringAtPos(Rule):
    """Ignores a transaction if the specified value is present in the specified index.

    For instance, given this csv entry:

    10.12.2022,mega supermarket,20US$

    and this rule:

    -  name: Ignore_By_ContainsStringAtPos
           ignore_string_contains_at_pos:
               - mega;1

    The row will be ignored, because the string "mega" is part of
    the index at position 1.

    Note that this rule supports multiple string specifications.

    Example:
        -  name: Ignore_By_ContainsStringAtPos
           ignore_string_contains_at_pos:
               - val;3
               - another val;6
    """

    def execute(
        self,
        csv_line: Dict[str, str],
        transaction: Transaction,
        rule_def: Dict[str, Any],
    ) -> RuleResult:
        """Execute the rule."""
        self.fail_if_attribute_missing(rule_def, "ignore_string_contains_at_pos")

        for ignorable in rule_def.get("ignore_string_contains_at_pos"):
            pos = int(ignorable.split(";")[1])
            str_to_ignore = ignorable.split(";")[0]
            if str_to_ignore.lower() in csv_line[pos].lower():
                return (True, None)
