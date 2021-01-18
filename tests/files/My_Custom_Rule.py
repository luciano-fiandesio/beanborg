from beanborg.rule_engine.rules import *

class My_Custom_Rule(Rule):
    def __init__(self, name, context): 
        
        # invoking the __init__ of the parent class  
        Rule.__init__(self, name, context)          

    def execute(self, csv_line, tx = None, ruleDef = None  ):
        
        self.checkAccountFromTo(ruleDef)

        if "Withdrawal".lower() in csv_line[self.context.tx_type_pos].lower():
            cashPosting = [Posting(
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
            return (True, tx._replace(postings=cashPosting))     

        return (False,tx)