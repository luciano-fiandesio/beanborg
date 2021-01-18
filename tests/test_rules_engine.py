from beanborg.rule_engine.rules_engine import RuleEngine
from beanborg.rule_engine.Context import *
from beanborg.rule_engine.decision_tables import *


def test_payee_replacement():

    rule_engine = make_rule_engine("testbank_payee.rules")

    entries = "31.10.2019,b,auszahlung,electro ford,x,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx.payee == "Ford Auto"


def test_asset_replacement():

    rule_engine = make_rule_engine("testbank_asset.rules")
    entries = "31.10.2019,b,auszahlung,electro ford,x,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx.postings[0].account == "Assets:Bob:Savings"


def test_expense_replacement():

    rule_engine = make_rule_engine("testbank_account.rules")
    entries = "31.10.2019,b,auszahlung,freshfood Bonn,x,ZZ03100400000608903100".split(
        ","
    )
    tx = rule_engine.execute(entries)
    assert tx.postings[1].account == "Expenses:Groceries"


def test_ignore():

    rule_engine = make_rule_engine("testbank_ignore.rules")
    entries = "31.10.2019,b,auszahlung,alfa,x,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx == None

    entries = "31.10.2019,b,auszahlung,beta,x,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx == None


def test_ignore_at_position():

    rule_engine = make_rule_engine("testbank_ignore_at_pos.rules")
    entries = "31.10.2019,b,auszahlung,alfa,waiting,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    assert tx == None


def test_custom_rule():

    rule_engine = make_rule_engine("testbank_custom.rules")
    entries = "31.10.2019,b,Withdrawal,alfa,waiting,ZZ03100400000608903100".split(",")
    tx = rule_engine.execute(entries)
    
    assert tx.postings[0].account == "Assets:UK:Alice:Savings"
    assert tx.postings[1].account == "Assets:UK:Alice:Cash"
    

def make_rule_engine(rule_file):
    return RuleEngine(
        Context(
            rules_dir="tests/files",
            account=None,
            date_fomat="%d.%m.%Y",
            default_expense="Expenses:Unknown",
            date_pos=0,
            payee_pos=3,
            tx_type_pos=2,
            account_pos=5,
            rules="tests/files/" + rule_file,
            assets=init_decision_table("tests/files/asset.rules"),
            accounts=init_decision_table("tests/files/account.rules"),
            payees=init_decision_table("tests/files/payee.rules"),
        )
    )
