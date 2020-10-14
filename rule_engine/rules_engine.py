#!/usr/bin/env python3

import sys
import traceback
from enum import Enum 
from beancount.core.data import Transaction, Posting, Amount, Close, Open, EMPTY_SET
from datetime import datetime
import unittest
import importlib
import yaml
from rule_engine.Context import Context
from rule_engine.rules import *
from dataclasses import dataclass

import os

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

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

    def execute(self, csv_line, transaction = None ):

        return (False,Transaction(
            meta=None,
            date=None,
            flag='*',
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
                meta=None),
            Posting(
                account=None,
                units=None,
                cost=None,
                price=None,
                flag=None,
                meta=None),
        ],
        ))

class RuleEngine:

    def __init__(self, ctx: Context):
        self._ctx = ctx
        self.rules = {}
        try:
            with open(os.getcwd() + '/' + self._ctx.rules) as f:
        
                yrules = yaml.load(f, Loader=yaml.FullLoader)['rules']
                for yrule in yrules :
                    rule_name = yrule["name"] # rule name
                    xfrom = yrule.get("from") # Account from
                    xto = yrule.get("to") # Account to
                    xpos = yrule.get("csv_index") # CSV index (base 0)
                    xignore = yrule.get("ignore_payee") # Payee string to ignore
                    xstring = yrule.get("csv_values") # semicolon separated strings
                    xignorepos = yrule.get("ignore_string_at_pos")
                    self.rules[rule_name] = RuleDef(globals()[rule_name], xfrom, xto, xpos, xignore, xstring, xignorepos)
        except KeyError as ke:
            sys.exit('The rule file references a rule that does not exist: ' + str(ke))
        except:
            sys.exit('The rule file ' + self._ctx.rules + ' is invalid!')
    
    def execute(self, csv_line):

        final, tx = Rule_Init('init', self._ctx).execute(csv_line)
        
        for key in self.rules:
            if not final:
                print("Executing rule: " + str(self.rules[key].rule))
                rulez = self.rules[key].rule(key, self._ctx)
                final, tx = rulez.execute(csv_line, tx, self.rules[key])
        
        return tx    


## TEST CASES        

class Rules_Engine_Test(unittest.TestCase):
        
    def setUp(self):
        rule_engine = RuleEngine(Context(
        date_fomat='%d.%m.%Y',
        default_expense='Expenses:Unknown',
        date_pos=0,
        payee_pos=3,
        tx_type_pos=2,
        account_pos=5,
        rules='rules/laura.commerzbank.rules',
        assets=init_decision_table('rules/asset.rules'),
        accounts=init_decision_table('rules/account.rules'),
        payees=init_decision_table('rules/payee.rules')))
        
        self.rule_engine = rule_engine

    def test_cash_rule(self):
        csv = '31.10.2019,b,auszahlung,a bc Bayer,x,DE03100400000608903100'
        entries = csv.split(',')
        tx = self.rule_engine.execute(entries)
        self.assertEqual(tx.postings[0].account, "Assets:DE:CB:Laura:Current")
        self.assertEqual(tx.postings[1].account, "Assets:DE:Laura:Cash")


    def test_salary_rule(self):
        
        csv = '31.10.2019,b,Gutschrift,a bc Bayer,x,DE03100400000608903100'
        entries = csv.split(',')
        tx = self.rule_engine.execute(entries)
        self.assertEqual(tx.postings[0].account, "Assets:DE:CB:Laura:Current")
        self.assertEqual(tx.postings[1].account, "Income:Salary:Bayer")

    def test_asset_replace(self):
        
        csv = '31.10.2019,b,Lastschrift,Amazon,x,DE03100400000608903100'
        entries = csv.split(',')
        tx = self.rule_engine.execute(entries)
        self.assertEqual(tx.postings[0].account, "Assets:DE:CB:Laura:Current")

    def test_expense_replace(self):
        
        csv = '31.10.2019,b,Lastschrift,EDEKA supermarket,x,DE03100400000608903100'
        entries = csv.split(',')
        tx = self.rule_engine.execute(entries)
        self.assertEqual(tx.postings[0].account, "Assets:DE:CB:Laura:Current")
        self.assertEqual(tx.postings[1].account, "Expenses:Groceries")

if __name__ == '__main__': 
    unittest.main() 