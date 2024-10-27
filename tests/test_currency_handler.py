from beanborg.handlers.amount_handler import AmountHandler
from beanborg.config import *
from beancount.core.number import D

def test_handler():

	config = init_config('tests/files/amount_handler.yaml', False)

	handler = AmountHandler()

	assert D("100.00") == handler.handle("100.00", config)
	assert D("22000.76") == handler.handle("22 000,76", config)
	assert D("22000.76") == handler.handle("22.000,76", config)
	assert D("1022000.76") == handler.handle("1022000,76", config)
	assert D("-1022000.76") == handler.handle("-1,022,000.76", config)
	assert D("1022000.00") == handler.handle("1022000", config)
	assert D("22000.76") == handler.handle("22 000,76$", config)
