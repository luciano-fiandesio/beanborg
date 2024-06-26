# -*- coding: utf-8 -*-

import abc
import fnmatch
import os
import sys

from beancount.core.data import Posting

from .Context import Context
from .decision_tables import init_decision_table, resolve_from_decision_table


class LookUpCache:
    """
    Simple cache for lookup tables
    """

    cache = dict()

    @staticmethod
    def init_decision_table(key, path):

        if key in LookUpCache.cache:
            return LookUpCache.cache[key]

        data = init_decision_table(path)
        LookUpCache.cache[key] = data
        return data


class Rule:
    __metaclass__ = abc.ABCMeta

    def __init__(self, name: str, context: Context):
        self.name = name
        self.context = context

    @abc.abstractmethod
    def execute(self, csv_line, transaction=None, ruleDef=None):

        return

    def checkAccountFromTo(self, ruleDef):
        if ruleDef.get("from") is None or ruleDef.get("to") is None:
            raise Exception(
                "Account from and to required for rule: {rule}".format(
                    rule=ruleDef.rule.__name__
                )
            )

    def failIfAttributeMissing(self, ruleDef, attributeName):
        if ruleDef.get(attributeName) is None:
            raise Exception(
                "Attribute {attribute_name} required for rule: {rule} ".format(
                    attribute_name=attributeName, rule=ruleDef.rule.__name__
                )
            )


class Set_Accounts(Rule):
    """
    Assign a from/to asset or account to a transaction, depending on the
    value of a given cvs index.

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

    def __init__(self, name, context):
        Rule.__init__(self, name, context)

    def execute(self, csv_line, tx, ruleDef=None):

        # current value at index for the current row
        # csv_field_val = csv_line[ruleDef.csv_index].lower()
        csv_field_val = csv_line[ruleDef.get("csv_index")].lower().strip()

        # values specified in the rule definition
        vals = ruleDef.get("csv_values").split(";")

        match = False
        for val in vals:
            # Use fnmatch to allow wildcard matching
            if fnmatch.fnmatch(csv_field_val, val.lower().strip()):
                match = True
                break

        if match:
            newPosting = [
                Posting(
                    account=ruleDef.get("from"),
                    units=None,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                Posting(
                    account=ruleDef.get("to"),
                    units=None,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]

            return (True, tx._replace(postings=newPosting))

        return (False, tx)


class Replace_Payee(Rule):
    """
    Replaces the name of the transaction counterparty
    (for instance: McDonald -> Mc Donald Restaurant)
    The rule file containing the substitution rules
    must be located in the rules folder and must be named "payee.rules"
    """

    def __init__(self, name, context):
        Rule.__init__(self, name, context)

    def execute(self, csv_line, tx, ruleDef=None):
        table = os.path.join(self.context.rules_dir, "payee.rules")
        if not os.path.isfile(table):
            print(
                "file: %s does not exist! - The 'Replace_Payee' rules \
                    requires the payee.rules file."
                % (table)
            )
            sys.exit(-1)

        return (
            False,
            tx._replace(
                payee=resolve_from_decision_table(
                    LookUpCache.init_decision_table("payee", table),
                    csv_line[self.context.payee_pos],
                    csv_line[self.context.payee_pos],
                )
            ),
        )


class Replace_Asset(Rule):
    """
    Assigns an account to a transaction, based on value of the 'account' index
    of a CSV file row.
    This rule is useful to assign the correct source account
    of a CSV transaction.

    The rule is based on the 'asset.rules' look-up file.
    If no 'asset.rules' file is found, the account
    will be resolved to "Assets:Unknown" or
    to the value of the property `rules.origin_account` of the config file.
    """

    def __init__(self, name, context):
        Rule.__init__(self, name, context)

    def execute(self, csv_line, tx=None, ruleDef=None):

        asset = None
        table = os.path.join(self.context.rules_dir, "asset.rules")
        if self.context.force_account:
            asset = self.context.force_account
        else:
            if not os.path.isfile(table):
                print(
                    "file: %s does not exist! - \
                        The 'Replace_Asset' rules requires the asset.rules \
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
            new_postings = [posting] + [tx.postings[1]]
            return (False, tx._replace(postings=new_postings))

        return (False, tx)


class Replace_Expense(Rule):
    """
    Categorizes a transaction by assigning the account
    extracted from a look-up table
    based on the 'payee_pos' index of a CSV file row.

    The rule is based on the 'payee.rules' look-up file.
    """

    def __init__(self, name, context):
        Rule.__init__(self, name, context)

    def execute(self, csv_line, tx=None, ruleDef=None):
        table = os.path.join(self.context.rules_dir, "account.rules")

        if not os.path.isfile(table):
            print(
                "file: % s does not exist! - The 'Replace_Expense' rules \
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
            new_postings = [tx.postings[0]] + [posting]
            return (False, tx._replace(postings=new_postings))

        return (False, tx)


class Ignore_By_Payee(Rule):
    def __init__(self, name, context):
        Rule.__init__(self, name, context)

    def execute(self, csv_line, tx=None, ruleDef=None):

        self.failIfAttributeMissing(ruleDef, "ignore_payee")
        for ignorablePayee in ruleDef.get("ignore_payee"):
            if ignorablePayee.lower() in csv_line[self.context.payee_pos].lower():
                return (True, None)

        return (False, tx)


class Ignore_By_StringAtPos(Rule):
    """
    Ignores a transaction based on the value of the specified index.

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

    def __init__(self, name, context):
        Rule.__init__(self, name, context)

    def execute(self, csv_line, tx=None, ruleDef=None):

        self.failIfAttributeMissing(ruleDef, "ignore_string_at_pos")
        for ignorable in ruleDef.get("ignore_string_at_pos"):
            pos = int(ignorable.split(";")[1])
            strToIgnore = ignorable.split(";")[0]

            if strToIgnore.lower().strip() == csv_line[pos].lower().strip():
                return (True, None)

        return (False, tx)


class Ignore_By_ContainsStringAtPos(Rule):
    """
    Ignores a transaction if the specified value is present
    in the specified index.
    For instance, given this csv entry:

    10.12.2022,mega supermarket,20US$

    and this rule:

    -  name: Ignore_By_ContainsStringAtPos
           ignore_string_at_pos:
               - mega;1

    The row will be ignored, because the string "mega" is part of
    the index at position 1.

    Note that this rule supports multiple string specifications.

    Example:
        -  name: Ignore_By_ContainsStringAtPos
           ignore_string_at_pos:
               - val;3
               - another val;6
    """

    def __init__(self, name, context):
        Rule.__init__(self, name, context)

    def execute(self, csv_line, tx=None, ruleDef=None):

        self.failIfAttributeMissing(ruleDef, "ignore_string_contains_at_pos")

        for ignorable in ruleDef.get("ignore_string_contains_at_pos"):
            pos = int(ignorable.split(";")[1])
            strToIgnore = ignorable.split(";")[0]
            if strToIgnore.lower() in csv_line[pos].lower():
                return (True, None)
