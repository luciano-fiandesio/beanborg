import os
import json
import traceback
import logging
from string import Template
from pathlib import Path
from openai import OpenAI
from rich.prompt import Confirm
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from beancount.parser.printer import format_entry
from beancount.core.data import Posting
from beanborg.utils.journal_utils import JournalUtils
from beanborg.utils.string_utils import StringUtils


class Classifier:

    def __init__(self):

        self.current_dir = Path(__file__).parent
        self.system_prompt_path = self.current_dir / 'prompts/system.txt'
        self.system_prompt = self.read_system_prompt()

    def has_no_category(self, tx, args) -> bool:

        return tx.postings[1].account == args.rules.default_expense

    def get_prompt_folder(self, prompt_folder):
        if isinstance(prompt_folder, tuple):
            return prompt_folder[0]
        elif isinstance(prompt_folder, str):
            return prompt_folder
        else:
            raise ValueError("Unexpected type for prompt_folder. Expected tuple or string.")

    def classify(self, txs, args):
        try:
            account_completer = FuzzyWordCompleter(JournalUtils().get_accounts(args.rules.bc_file))

            if not self.should_classify_transactions(txs, args):
                return

            system_prompt = self.generate_system_prompt(args)
            json_array = self.find_category(args, system_prompt, self.prepare(args, txs.getTransactions()))

            self.update_transactions(txs, args, json_array, account_completer)

        except Exception as e:
            print(f"An error occurred while classifying transactions: {str(e)}")
            print("Stack trace:")
            traceback.print_exc()

    def should_classify_transactions(self, txs, args):
        num_uncategorized = txs.count_no_category(args.rules.default_expense)
        if num_uncategorized == 0:
            return False

        return Confirm.ask(
            f'\n[red]You have [bold]{num_uncategorized}[/bold] transactions without a category. '
            f'Do you want to fix them now?[/red]'
        )

    def generate_system_prompt(self, args):
        prompt_folder = self.get_prompt_folder(args.classifier.prompt_folder)
        prompt_folder_path = os.path.join(os.getcwd(), prompt_folder)
        values = {
            'categories': self.read_file_content(prompt_folder_path, "categories.txt"),
            'rules': self.read_file_content(prompt_folder_path, "rules.txt")
        }

        system_template = Template(self.system_prompt)
        return system_template.substitute(values)

    def update_transactions(self, txs, args, json_array, account_completer):
        default_category = args.rules.default_expense

        for i, tx in enumerate(txs.getTransactions()):
            if not self.has_no_category(tx, args):
                continue

            guess = self.get_category_by_id(json_array, tx.meta["md5"]) or default_category

            print(format_entry(tx))
            text = prompt(
                'Enter account: ',
                completer=account_completer,
                complete_while_typing=True,
                default=guess
            )

            posting = Posting(text, None, None, None, None, None)
            new_postings = [tx.postings[0]] + [posting]
            txs.getTransactions()[i] = tx._replace(postings=new_postings)

    def get_category_by_id(self, transactions_dict, target_id):
        transactions_list = transactions_dict.get('transactions', [])
        for transaction in transactions_list:
            if transaction['id'] == target_id:
                return transaction['category']
        return None  # Return None if the transaction is not found

    def prepare(self, args, transactions):
        json_array = [
            self.extract_transaction_info(transaction)
            for transaction in transactions
            if self.has_no_category(transaction, args)
        ]
        return json.dumps(json_array, indent=4)

    def extract_transaction_info(self, transaction):
        transaction_id = transaction.meta["md5"]
        date = str(transaction.date)
        description = self.clean_description(transaction.payee)
        amount, currency = self.get_amount_and_currency(transaction.postings)

        return {
            "id": transaction_id,
            "date": date,
            "description": description,
            "amount": f"{amount:.2f}",
            "currency": currency
        }

    def clean_description(self, description):
        return StringUtils.strip_digits(description.strip())

    def get_amount_and_currency(self, postings):
        for posting in postings:
            if posting.units is not None:
                amount = abs(posting.units.number)
                currency = posting.units.currency
                return amount, currency
        return None, None

    def read_system_prompt(self):
        with open(self.system_prompt_path, 'r') as file:
            system_prompt = file.read()
        return system_prompt

    def read_file_content(self, path, file_name):
        file_path = os.path.join(path, file_name)

        try:
            with open(file_path, 'r') as file:
                content = file.read()
            return content
        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
            return None
        except IOError:
            print(f"An error occurred while reading the file '{file_path}'.")
            return None

    def find_category(self, args, system_prompt, json_transactions):
        
        print("System prompt: ", system_prompt)
        print("Transactions: ", json_transactions)
        
        try:
            client = OpenAI()
            response = client.chat.completions.create(
                model=args.classifier.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": json_transactions
                    }
                ],
                temperature=0.7,
                top_p=1
            )

            if response.choices and response.choices[0].message:
                array_response = response.choices[0].message.content
                
                try:
                    print("Array response: ", array_response)
                    return json.loads(array_response)
                except json.JSONDecodeError as e:
                    logging.error(f"Error parsing JSON response: {str(e)}")
                    logging.error(f"Response content: {array_response}")
                    return []
            else:
                logging.warning("Unexpected response format from OpenAI API")
                return []

        except Exception as e:
            logging.error(f"Error occurred while finding category: {str(e)}")
            return []
