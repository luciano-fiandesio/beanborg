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
from typing import Dict, List
import os
import re
import importlib
from importlib import import_module
import fnmatch

__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))


@dataclass
class RuleDef:
    rule: str
    attributes: Dict[str,List[str]]

    def get(self, key):
        return self.attributes[key]





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

    def handle(self, cr):

        return cr

    def __init__(self, ctx: Context):

        self._ctx = ctx
        self.rules = {}

        custom_rules = self.load_custom_rules()

        if (self._ctx.ruleset == None):
            print(u"\u26A0" + " no rules file spefified for this financial institution")
            self.rules = {}
        else:
            for yrule in self._ctx.ruleset:
                rule_props = {}
                for key in yrule:
                    if key == "name":
                        rule_name = yrule["name"]
                    else:
                        rule_props[key] = yrule.get(key)

                if rule_name in custom_rules:
                    self.rules[rule_name] = RuleDef(
                        custom_rules[rule_name],
                        rule_props
                    )
                else:
                    self.rules[rule_name] = RuleDef(
                        globals()[rule_name]
,                        rule_props
                    )
        # assign default rules, if they are not already specified
        if ctx.rules_dir: # do not auto-add if there is no rules folder!
            if 'Replace_Asset' not in self.rules:
                self.rules['Replace_Asset'] = RuleDef(
                            globals()['Replace_Asset'],
                            None
                        )


    def load_custom_rules(self):

        custom_rulez = {}
        if self._ctx.rules_dir != None:
            custom_rules_path = os.path.join(os.getcwd(), self._ctx.rules_dir)
            if not os.path.isdir(custom_rules_path):
                if self._ctx.debug:
                    print("Custom rules folder not found...ignoring")
                return custom_rulez
            sys.path.append(custom_rules_path)
            custom_rules = fnmatch.filter(
                os.listdir(custom_rules_path), "*.py"
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
                if self._ctx.debug:
                    print("Executing rule: " + str(self.rules[key].rule))
                rulez = self.rules[key].rule(key, self._ctx)
                final, tx = rulez.execute(csv_line, tx, self.rules[key])

        return tx
