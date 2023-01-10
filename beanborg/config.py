import os
import sys
import yaml


class Rules:
    def __init__(
        self,
        bc_file=None,
        rules_folder=None,
        account=None,
        currency=None,
        default_expense=None,
        force_negative=None,
        invert_negative=None,
        origin_account=None,
        ruleset=[],
        advanced_duplicate_detection=None
    ):
        self.bc_file = bc_file
        self.rules_folder = rules_folder
        self.account = account
        self.currency = currency
        self.default_expense = default_expense
        self.force_negative = force_negative
        self.invert_negative = invert_negative
        self.origin_account = origin_account
        self.ruleset = ruleset
        self.advanced_duplicate_detection = advanced_duplicate_detection


class Indexes:
    def __init__(
        self,
        date=None,
        counterparty=None,
        amount=None,
        account=None,
        currency=None,
        tx_type=None,
        amount_in=None,
        narration=None,
    ):
        self.date = date
        self.counterparty = counterparty
        self.amount = amount
        self.account = account
        self.currency = currency
        self.tx_type = tx_type
        self.amount_in = amount_in
        self.narration = narration


class Csv:
    def __init__(
        self,
        download_path,
        name,
        ref,
        separator=None,
        date_format=None,
        skip=None,
        target=None,
        archive=None,
        post_script_path=None,
    ):
        self.download_path = download_path
        self.name = name
        self.ref = ref
        self.separator = separator
        self.date_format = date_format
        self.skip = skip
        self.target = target
        self.archive = archive
        self.post_script_path = post_script_path


class Config:
    def __init__(self, csv, indexes, rules, debug=False):
        self.csv = csv
        self.indexes = indexes
        self.rules = rules
        self.debug = debug

    def load(loader, node):
        values = loader.construct_mapping(node, deep=True)

        csv_data = values["csv"]

        csv = Csv(
            csv_data["download_path"],
            csv_data["name"],
            csv_data["bank_ref"],
            csv_data.get("separator", ","),
            csv_data["date_format"],
            csv_data.get("skip", 1),
            csv_data.get("target", "tmp"),
            csv_data.get("archive_path", "archive"),
            csv_data.get("post_move_script"),
        )

        idx = values.get("indexes", dict())

        indexes = Indexes(
            idx.get("date", 0),
            idx.get("counterparty", 3),
            idx.get("amount", 4),
            idx.get("account", 1),
            idx.get("currency", 5),
            idx.get("tx_type", 2),
            idx.get("amount_in", None),
            idx.get("narration", None),
        )

        rls = values.get("rules", dict())

        rules = Rules(
            rls.get("beancount_file", "main.ldg"),
            rls.get("rules_folder", "rules"),
            rls.get("account", None),
            rls.get("currency", None),
            rls.get("default_expense", "Expenses:Unknown"),
            rls.get("force_negative", False),
            rls.get("invert_negative", False),
            rls.get("origin_account", None),
            rls.get("ruleset", []),
            rls.get("advanced_duplicate_detection", True)
        )

        return Config(csv, indexes, rules)


def init_config(file, debug):

    yaml.add_constructor(u"!Config", Config.load)

    if not os.path.isfile(file):
        print("file: %s does not exist!" % (file))
        sys.exit(-1)

    with open(file, "r") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    config.debug = debug
    return config
