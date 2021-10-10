from beanborg.rule_engine.rules_engine import RuleEngine
from beanborg.rule_engine.Context import *
from beanborg.rule_engine.decision_tables import *
from beanborg.config import *

def test_config1():

    config = init_config('tests/files/bank1.yaml', False)

    assert config.csv.download_path == "/Users/luciano/Desktop"
    assert config.csv.name == "bbk_statement"
    assert config.csv.ref == "bbk"
    assert config.csv.target == 'tmp2'
    assert config.csv.archive == 'archive2'
    assert config.csv.separator == '|'
    assert config.csv.date_format == '%d/%m/%Y'
    assert config.csv.skip == 3

    assert config.indexes.date == 8
    assert config.indexes.counterparty == 9
    assert config.indexes.amount == 10
    assert config.indexes.account == 11
    assert config.indexes.currency == 12
    assert config.indexes.tx_type == 13
    assert config.indexes.amount_in == 14

    assert config.rules.bc_file == 'main1.ldg'
    assert config.rules.account == '1234567'
    assert config.rules.currency == 'GBP'
    assert config.rules.default_expense == "Expense:Magic"
    assert config.rules.force_negative == True
    assert config.rules.invert_negative == True

    assert len(config.rules.ruleset) == 1
    assert config.rules.ruleset[0]['name'] == 'hello_rule'
    assert config.rules.ruleset[0]['test'] == 1
    
    