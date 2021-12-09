from beanborg.rule_engine.decision_tables import *


def test_equal_value():
    table = {}
    table["superman"] = ("equals", "batman")
    assert "batman" == resolve_from_decision_table(table, "superman", "mini")

def test_equal_value_different_case():
    table = {}
    table["superman"] = ("equals", "batman")
    assert "Batman" != resolve_from_decision_table(table, "superman", "mini")

def test_equal_value_ignore_different_case():
    table = {}
    table["rewe"] = ("equals_ic", "Expenses:Groceries")
    assert "Expenses:Groceries" == resolve_from_decision_table(table, "rewe", "Expenses:Unknown")

def test_startsWith_value():
    table = {}
    table["superman"] = ("startsWith", "batman")
    assert "batman" == resolve_from_decision_table(table, "superman_is_cool", "mini")

def test_endsWith_value():
    table = {}
    table["superman"] = ("endsWith", "batman")
    assert "batman" == resolve_from_decision_table(table, "hello_superman", "mini")

def test_contains_value():
    table = {}
    table["superman"] = ("contains", "batman")
    assert "batman" == resolve_from_decision_table(
        table, "hello_superman_hello", "mini"
    )

def test_contains_value_ignore_case():
    table = {}
    table["rewe"] = ("contains_ic", "Expenses:Groceries")
    
    assert "Expenses:Groceries" == resolve_from_decision_table(
        table, "card transaction - supermarket REWE", "Expenses:Unknown"
    )

def test_loadfile():
    table = init_decision_table("tests/files/payee_with_comments.rules")
    assert table["ford"] != None
    assert table["ford"][0] == "contains"
    assert table["ford"][1] == "Ford Auto"
    