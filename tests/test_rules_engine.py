from beanborg.rule_engine.rules_engine import RuleEngine
from beanborg.rule_engine.Context import *
from beanborg.rule_engine.decision_tables import *
from beanborg.config import *

def test_payee_replacement():

    rule_engine = make_rule_engine('tests/files/bank1_replace_counterparty.yaml')

    entries = "31.10.2019,b,auszahlung,electro ford,x,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx.payee == "Ford Auto"

def test_asset_replacement():

    rule_engine = make_rule_engine('tests/files/bank1_replace_asset.yaml')
    entries = "31.10.2019,b,auszahlung,electro ford,x,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx.postings[0].account == "Assets:Bob:Savings"

def test_expense_replacement():

    rule_engine = make_rule_engine('tests/files/bank1_replace_expense.yaml')
    entries = "31.10.2019,b,auszahlung,freshfood Bonn,x,ZZ03100400000608903100".split(
        ","
    )
    tx = rule_engine.execute(entries)
    assert tx.postings[1].account == "Expenses:Groceries"

def test_expense_replacement2():

    rule_engine = make_rule_engine('tests/files/bank1_replace_expense2.yaml')
    entries = "31.10.2019,b,auszahlung,books,x,ZZ03100400000608903100".split(
        ","
    )
    tx = rule_engine.execute(entries)
    assert tx.postings[1].account == "Expenses:Multimedia:Books"

def test_ignore():

    rule_engine = make_rule_engine('tests/files/bank1_ignore_by_counterparty.yaml')
    
    entries = "31.10.2019,b,auszahlung,alfa,x,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx == None

    entries = "31.10.2019,b,auszahlung,beta,x,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx == None

def test_ignore_at_position():

    rule_engine = make_rule_engine('tests/files/bank1_ignore_at_pos.yaml')
    entries = "31.10.2019,b,auszahlung,alfa,waiting,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx == None

def test_ignore_by_contains_string_at_position():
    rule_engine = make_rule_engine('tests/files/bank1_ignore_contains_string_at_pos.yaml')
    entries = "31.10.2019,b,auszahlung,alfa,this is waiting alfa,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx == None


def test_custom_rule():

    rule_engine = make_rule_engine('tests/files/bank1_custom_rule.yaml')
    entries = "31.10.2019,b,Withdrawal,alfa,waiting,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    
    assert tx.postings[0].account == "Assets:UK:Alice:Savings"
    assert tx.postings[1].account == "Assets:UK:Alice:Cash"
    
def test_no_rulefile():

    rule_engine = RuleEngine(
        Context(
            rules_dir=None,
            account=None,
            date_fomat="%d.%m.%Y",
            default_expense="Expenses:Unknown",
            date_pos=0,
            payee_pos=3,
            tx_type_pos=2,
            narration_pos=-1,
            account_pos=5,
            ruleset=None,
            force_account=None,
            debug=False
        )
    )

    entries = "31.10.2019,b,Withdrawal,alfa,waiting,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)

    # no exception - the transaction is empty
    assert tx

def make_rule_engine(config_file):
    config = init_config(config_file, False)
    return RuleEngine(
        Context(
            ruleset=config.rules.ruleset,
            rules_dir="tests/files",
            account=config.rules.account,
            date_fomat="%d.%m.%Y",
            default_expense="Expenses:Unknown",
            date_pos=0,
            payee_pos=3,
            tx_type_pos=2,
            narration_pos=-1,
            account_pos=5,
            force_account=None,
            debug=False
        )
    )
