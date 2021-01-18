#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import inspect
import traceback
from enum import Enum
from beancount.core.data import Transaction, Posting, Amount, Close, Open, EMPTY_SET
from datetime import datetime
import importlib
import yaml
from .Context import Context
from .rules import *
from dataclasses import dataclass

import os
import re
import importlib
from importlib import import_module
import fnmatch

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


@dataclass
class RuleDef:
    rule: str
    account_from: str
    account_to: str
    csv_index: int
    ignore_payee: str
    csv_value: str
    ignore_string_at_pos: str


class Rule_Init(Rule):
    def __init__(self, name, context):
        Rule.__init__(self, name, context)

    def execute(self, csv_line, transaction=None):

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
                postings=[
                    Posting(
                        account=None,
                        units=None,
                        cost=None,
                        price=None,
                        flag=None,
                        meta=None,
                    ),
                    Posting(
                        account=None,
                        units=None,
                        cost=None,
                        price=None,
                        flag=None,
                        meta=None,
                    ),
                ],
            ),
        )


class RuleEngine:
    def __init__(self, ctx: Context):

        self._ctx = ctx
        self.rules = {}

        custom_rules = self.load_custom_rules()

        if (self._ctx.rules == None):
            print(u"\u26A0" + " no rules file spefified for this financial institution")
            self.rules = {}
        else:    
            try:
                with open(os.getcwd() + "/" + self._ctx.rules) as f:

                    yrules = yaml.load(f, Loader=yaml.FullLoader)["rules"]
                    for yrule in yrules:

                        rule_name = yrule["name"]  # rule name
                        xfrom = yrule.get("from")  # Account from
                        xto = yrule.get("to")  # Account to
                        xpos = yrule.get("csv_index")  # CSV index (base 0)
                        # Payee string to ignore
                        xignore = yrule.get("ignore_payee")
                        # semicolon separated strings
                        xstring = yrule.get("csv_values")
                        xignorepos = yrule.get("ignore_string_at_pos")

                        if rule_name in custom_rules:
                            # print('custom-rule')
                            self.rules[rule_name] = RuleDef(
                                custom_rules[rule_name],
                                xfrom,
                                xto,
                                xpos,
                                xignore,
                                xstring,
                                xignorepos,
                            )
                        else:
                            self.rules[rule_name] = RuleDef(
                                globals()[rule_name],
                                xfrom,
                                xto,
                                xpos,
                                xignore,
                                xstring,
                                xignorepos,
                            )

            except KeyError as ke:
                sys.exit("The rule file references a rule that does not exist: " + str(ke))

            except Exception as e:
                # print(str(e))
                sys.exit("The rule file " + self._ctx.rules + " is invalid!")

    def load_custom_rules(self):

        custom_rulez = {}
        if self._ctx.rules_dir != None:
            sys.path.append(os.getcwd() + "/" + self._ctx.rules_dir)
            custom_rules = fnmatch.filter(
                os.listdir(os.getcwd() + "/" + self._ctx.rules_dir), "*.py"
            )
            for r in custom_rules:
                mod_name = r[:-3]
                mod = __import__(mod_name, globals={})
                class_ = getattr(mod, mod_name)
                # TODO check if custom rule is of type rule before adding
                custom_rulez[mod_name] = class_

        return custom_rulez

    def execute(self, csv_line):

        final, tx = Rule_Init("init", self._ctx).execute(csv_line)

        for key in self.rules:
            if not final:
                print("Executing rule: " + str(self.rules[key].rule))
                rulez = self.rules[key].rule(key, self._ctx)
                final, tx = rulez.execute(csv_line, tx, self.rules[key])

        return tx
