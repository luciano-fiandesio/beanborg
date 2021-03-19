import yaml
import argparse

class Rules(object):

    def __init__(self, bc_file=None, rules_folder=None, rules_file=None, account=None, currency=None, default_expense=None, force_negative=None, invert_negative=None):
        self.bc_file = bc_file
        self.rules_folder = rules_folder
        self.rules_file = rules_file
        self.account = account
        self.currency = currency
        self.default_expense = default_expense
        self.force_negative = force_negative
        self.invert_negative = invert_negative

class Indexes(object):

    def __init__(self, date=None, payee=None, amount=None, account=None, currency=None, tx_type=None, amount_in=None):
        self.date = date
        self.payee = payee
        self.amount = amount
        self.account = amount
        self.currency = currency
        self.tx_type = tx_type
        self.amount_in = amount_in
        

class Csv(object):

    def __init__(self, download_path, name, ref, separator=None, currency_sep=None, date_format=None, skip=None, target=None):
        self.download_path = download_path
        self.name = name
        self.ref = ref
        self.separator = separator
        self.currency_sep = currency_sep
        self.date_format = date_format
        self.skip = skip
        self.target = target

class Config(object):

    def __init__(self, csv, indexes, rules, debug=False):
        self.csv = csv
        self.indexes = indexes
        self.rules = rules
        self.debug = debug
            
    def load(loader, node):
        values = loader.construct_mapping(node, deep=True)
        
        csv_data = values['csv']

        csv = Csv(
            csv_data['download_path'],
            csv_data['name'],
            csv_data['bank_ref'],
            csv_data.get('separator', ','),
            csv_data.get('currency_sep', '.'),
            csv_data['date_format'],
            csv_data.get('skip', 1),
            csv_data.get('target', 'tmp')
        )

        idx = values['indexes'] 
        
        indexes = Indexes(
            idx.get('date', 0), 
            idx.get('payee', 3),
            idx.get('amount', 4),
            idx.get('currency', 5),
            idx.get('tx_type', 2),
            idx.get('amount_in', None)
        )

        rls = values['rules']
        rules = Rules(
            rls.get('beancount_file', 'main.ldg'),
            rls.get('rules_folder', 'rules'),
            rls.get('rules_file', csv.ref + '.rules'),
            rls.get('account', None),
            rls.get('currency', None),
            rls.get('default_expense', 'Expense:Unknown'),
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

    parser.add_argument(
        "-v", "--debug", required=False, default=False, action="store_true"
    )

    args = parser.parse_args()


    with open(args.file, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    config.debug = args.debug    
    return config


if __name__ == '__main__':
    a = Config("a", "b", "c")

    print("path: %s, name: %s, ref: %s, target: %s" %
          (a.path, a.name, a.ref, a.target))

    a = Config.mover("pippo", "pluto", "paperino")

    print("path: %s, name: %s, ref: %s, target: %s" %
          (a.path, a.name, a.ref, a.target))
