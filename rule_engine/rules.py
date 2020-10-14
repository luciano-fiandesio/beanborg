import abc
from rule_engine.Context import Context
from beancount.core.data import Transaction, Posting, Amount, Close, Open
from rule_engine.decision_tables import *

class Rule:
    __metaclass__ = abc.ABCMeta
    def __init__(self, name: str, context: Context):
        self.name = name
        self.context = context

    @abc.abstractmethod
    def execute(self, csv_line, transaction = None, ruleDef = None ):

        return 
    
    def checkAccountFromTo(self, ruleDef):
        if ruleDef.account_from is None or ruleDef.account_to is  None:
            raise Exception('Account from and to required for rule ' + ruleDef.rule.__name__) 

    def checkIgnorePayee(self, ruleDef):
        if ruleDef.ignore_payee is None:
            raise Exception('Ignore by payee (ignore_payee) required for rule ' + ruleDef.rule.__name__) 

class CB_Salary(Rule):

    def __init__(self, name, context): 
        
        # invoking the __init__ of the parent class  
        Rule.__init__(self, name, context)          

    def execute(self, csv_line, tx = None,ruleDef = None ):


        if csv_line[self.context.tx_type_pos].lower() == "Gutschrift".lower() and \
        "Bayer".lower() in csv_line[self.context.payee_pos].lower():

            salaryPosting = [Posting(
                account='Assets:DE:CB:Laura:Current',
                units=None,
                cost=None,
                price=None,
                flag=None,
                meta=None),
            Posting(
                account='Income:Salary:Bayer',
                units=None,
                cost=None,
                price=None,
                flag=None,
                meta=None)]

            return (True, tx._replace(postings=salaryPosting))  

        return (False, tx)


class Set_Accounts(Rule):

    def __init__(self, name, context): 
        Rule.__init__(self, name, context)

    def execute(self, csv_line, tx ,ruleDef = None):
        
        # current value at index for the current row
        csv_field_val = csv_line[ruleDef.csv_index].lower()

        # values specified in the rule definition
        vals = ruleDef.csv_value.split(";")

        match = False
        for val in vals:
            if val.lower() in csv_field_val:
                match = True

        if match:
            newPosting = [Posting(
                account=ruleDef.account_from,
                units=None,
                cost=None,
                price=None,
                flag=None,
                meta=None),
            Posting(
                account=ruleDef.account_to,
                units=None,
                cost=None,
                price=None,
                flag=None,
                meta=None)]

            return (True, tx._replace(postings=newPosting))     

        return (False,tx)                

class Replace_Payee(Rule):
    def __init__(self, name, context): 
        Rule.__init__(self, name, context)          

    def execute(self, csv_line, tx ,ruleDef = None):
        
        return (False, tx._replace(payee=resolve_from_decision_table(self.context.payees, csv_line[self.context.payee_pos], 
            csv_line[self.context.payee_pos])))     

class Replace_Asset(Rule):
    def __init__(self, name, context): 
        Rule.__init__(self, name, context)   

    def execute(self, csv_line, tx = None,ruleDef = None ):
        asset = resolve_from_decision_table(self.context.assets, self.context.account if self.context.account is not None else csv_line[self.context.account_pos], 'Assets:Unknown')
        if asset:
            posting = Posting(asset, None, None, None, None, None)
            new_postings = [posting] + [tx.postings[1]]
            return (False, tx._replace(postings=new_postings))
            
        return (False, tx)  

class Replace_Expense(Rule):
    def __init__(self, name, context): 
        Rule.__init__(self, name, context)   

    def execute(self, csv_line, tx = None,ruleDef = None ):
        expense = resolve_from_decision_table(self.context.accounts, csv_line[self.context.payee_pos], self.context.default_expense)
        if expense:
            posting = Posting(expense, None, None, None, None, None)
            new_postings = [tx.postings[0]] + [posting]
            return (False, tx._replace(postings=new_postings))
            
        return (False, tx)            

class Ignore_By_Payee(Rule):
    def __init__(self, name, context): 
        Rule.__init__(self, name, context)   

    def execute(self, csv_line, tx = None, ruleDef = None ):

        self.checkIgnorePayee(ruleDef)
        for ignorablePayee in ruleDef.ignore_payee:
            if ignorablePayee.lower() in csv_line[self.context.payee_pos].lower():
                return (True, None) 
            
        return (False, tx)

class Ignore_By_StringAtPos(Rule):
    def __init__(self, name, context): 
        Rule.__init__(self, name, context)   

    def execute(self, csv_line, tx = None, ruleDef = None ):

        for ignorable in ruleDef.ignore_string_at_pos:
            pos = int(ignorable.split(';')[1])
            strToIgnore = ignorable.split(';')[0]
            
            if strToIgnore.lower() == csv_line[pos].lower():
                return (True, None) 
            
        return (False, tx)
