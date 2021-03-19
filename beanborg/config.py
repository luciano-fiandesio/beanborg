import yaml
import argparse

class Rules(object):

	def __init__(self, date_format=None, rules_folder=None, rules_file=None, account=None, currency=None, currency_sep=None, skip=None, force_negative=None, invert_negative=None):
		self.date_format = date_format
		self.rules_folder = rules_folder
		self.rules_file = rules_file
		self.account = account
		self.currency = currency
		self.currency_sep = currency_sep
		self.skip = skip
		self.force_negative = force_negative
		self.invert_negative = invert_negative

class Indexes(object):

	def __init__(self, date=None, payee=None, amount=None, account=None, currency=None, tx_type=None, account_in=None):
		self.date = date
		self.payee = payee
		self.amount = amount
		self.account = amount
		self.currency = currency
		self.tx_type = tx_type
		self.account_in = account_in
		

class Csv(object):

	def __init__(self, download_path, name, ref, target=None):
		self.download_path = download_path
		self.name = name
		self.ref = ref
		self.target = target

class Config(object):

    def __init__(self, csv, indexes, rules):
        self.csv = csv
        self.indexes = indexes
        self.rules = rules
        	
    def load(loader, node):
        values = loader.construct_mapping(node, deep=True)
        
        csv_data = values['csv']

        csv = Csv(
        	csv_data['download_path'],
			csv_data['name'],
        	csv_data['bank_ref'],
        	csv_data.get('target', 'tmp')
        )

        idx = values['indexes']	
        
        indexes = Indexes(
        	idx.get('date', 0), 
        	idx.get('payee', 3),
        	idx.get('amount', 4),
        	idx.get('currency', 5),
        	idx.get('tx_type', 2),
        	idx.get('account_in', None)
        )

        rls = values['rules']
        rules = Rules(
        	rls['date_format'],
        	rls.get('rules_folder', 'rules'),
        	rls.get('rules_file', csv.ref + '.rules'),
        	rls.get('account', None),
        	rls.get('currency', None),
        	rls.get('currency_sep', '.'),
        	rls.get('skip', 1),
        	rls.get('force_negative', False),
			rls.get('invert_negative', False)
        )


        return Config(csv, indexes, rules)


def init_config(help_message):

    yaml.add_constructor(u'!Config', Config.load)

    parser = argparse.ArgumentParser(
        description=help_message
    )

    parser.add_argument(
        "-f",
        "--file",
        help="Configuration file to load",
        required=True,
    )

    args = parser.parse_args()

    with open(args.file, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    return config


if __name__ == '__main__':
    a = Config("a", "b", "c")

    print("path: %s, name: %s, ref: %s, target: %s" %
          (a.path, a.name, a.ref, a.target))

    a = Config.mover("pippo", "pluto", "paperino")

    print("path: %s, name: %s, ref: %s, target: %s" %
          (a.path, a.name, a.ref, a.target))
