from beanborg.utils.duplicate_detector import *
from beancount import loader

def test_duplication():

    # load dummy ledger file
    txs = init_duplication_store('1234.ldg', 'tests/files/1234.ldg' )
    
    # load a second dummy ledger file, that contains an identical transaction
    entries, _, _ = loader.load_file('tests/files/_1234.ldg')
    for entry in entries:
        tup = to_tuple(entry)
        assert (hash_tuple(tup) in txs)


    
