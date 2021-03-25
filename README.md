Beanborg automatically imports financial transactions from external CSV files into the [Beancount](http://furius.ca/beancount/) bookkeeping system.

## Requirements

- Python 3
- Beancount v2

## Goals and key features

Beanborg has two main design goals:

- automatic matching of transaction data with the correct Expense accounts
- speed, the tool is designed to process several financial CSV file in few seconds

Given the following transaction from a CSV file:

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Beanborg import the transaction in Beancount and assign the Account "Expense:Grocery" to the transaction:

```
2020-11-04 * "Fresh Food Inc." ""
csv: "04.11.2020,04.11.2020,Direct Debit,Fresh Food,-21,30,EUR,0000001,UK0000001444555"
md5: "60a54f6ed13ae7b7e70fd475eb677511"
Assets:Bank1:Bob:Current  -21.30 EUR
Expenses:Grocery      
```

Other features:

- sophisticated and extendible rule based system
- avoid duplicates during import 
- high degree of configurability
- smart archiving function: when archiving a CSV file, the file is renamed using the start and end date of the CSV file

## Installation

Currently, it is not possible to install beanborg using `pip`. This feature will be added soon. Stay tuned!

### Installation steps

Clone this repository and add the `beanborg` folder to your shell's path.

```
git clone https://github.com/luciano-fiandesio/beanborg

# Bash: add the following to your ~/.profile or ~/.bash_profile

PATH=$PATH:~/../beanborg/beaborg

# Fish: add the following to your config.fish file 

fish_add_path ~/../beanborg/beanborg
```

## Workflow

Beanborg is based on a very specific workflow, which may or may not work for you.

The workflow is based on 3 distinct stages:

- Move a CSV file downloaded from a bank/financial institution website into the stage area
- Import the CSV file into Beancount ledger and automatically categorize the transactions
- Move the bank CSV file into archive area

The first stage is executed by the `bb_mover.py` script.

The second stage is executed by the `bb_import.py` script.

The third stage is executed by the `bb_clean.py` script.

### Configuration

Each financial institution from which data will be imported, must have a dedicated yaml configuration file.
The configuration file is used by the import scripts to determine the CSV file structure and other information, including which rules to apply.

### Structure of a configuration file

A Beanborg configuration must start with the `--- !Config` tag and has 3 main sections:

#### csv

The `csv` section of the configuration file determines the options related to the structure and localtion of the CVS file.
These are the list of options for the `csv` section:

| Property      | Description                                                                                                                                                                                      | Default | Example             |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|---------------------|
| download_path | Full path to the folder to which the CSV is downloaded to at the beginning of the import process. This option is only required by the `bb_mover` script.                                      |         | "/home/john/download" |
| name          | The name of the CSV file, at the time of download. Note that the name can be partial. For instance, is the CSV file is named "bank1-statement-03-2020", the `name` can be simply set to `bank1`. This option is only required by the `bb_mover` script.                                                         |         | `bank1`             |
| ref           | Once the CVS file is imported into the staging area, it gets renamed using the value of `ref`. It is recommended to use a short string to identify the financial institution. This option is used by all the scripts.                                                                                   |         | `com`               |
| separator     | The field delimiter used in the financial institution's CSV file.        | ,       |                     |
| currency_sep  | The decimal separator used in the CSV file                                                                                                                                                       | .       |                     |
| date_format   | Date format used in the CVS file. The format is based on  strftime directives: https://strftime.org/. Note that the value must be in quotes                                                      |         | "%d/%m/%Y"          |
| skip          | Number of lines of the CSV file to skip during import                                                                                                    | 1       |                     |
| target        | The folder name or path in which the CSV file is moved to during the first stage.    s                                                                                                            | tmp     |                     |
| archive       | The folder name of path in which the CSV file is archived during the archive stage                                                                                                               | archive |                     |

#### indexes

The `indexes` section of the configuration file allows to map each CSV "column" (or index) to the information required to parse and import the data. In other words, each option is used by Beanborg to determine where the `date` or `amount` of each transaction is located on the CVS file.

Note that the first index starts from `0`.

| Property     | Description                                                                                                                                                                                      | Default |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| date         | The index corresponding to the date of the transaction                                                                                                                                           | 0       |
| counterparty | The index corresponding to the name of the counterparty of the transaction                                                                                                                       | 3       |
| amount       | The index corresponding to the amount of the transaction (either debit or credit)                                                                                                                | 4       |
| account      | The index corresponding to the account of the transaction (e.g. the IBAN or ABA code)                                                                                      | 1       |
| currency     | The index corresponding to the currency of the transaction                                                                                                                                       | 5       |
| tx_type      | The index corresponding to the transaction type                                                                                                                                                  | 2       |
| amount_in    | Some financial institutions, use separate indexes for debit and credit. In this case, it is possible to specify the index for the index corresponding to the credited amount |         |


#### rules



Each Beancount asset (bank account, credit card, etc.) to which you want to import data into must be declared in the main Beancount ledger.

```
2019-01-01 open Assets:Bob:Savings      EUR
```

#### Sample configuration file

```
--- !Config
csv:
  download_path: "/home/mike/downloads"
  name: wells-fargo
  bank_ref: wfa
  date_format: "%d/%m/%Y"
  skip: 1
  
indexes:
  date:   1
  amount: 2
  counterparty: 6

rules:
  beancount_file: 'main-ledger.ldg'
  rules_file: well-fargo.rules
  account: 565444499
  currency: USD
```

### Rules

The beanborg's rules engine comes with a number of preexisting rules. Rules are always referenced by name and can be used to assign an account to a transaction, ignore a transaction or replace the name of a transaction's conterparty.
Some rules require a look-up table file in order to find the right value and execute the rule action.

A look-up table file is also a CSV file, composed of 3 columns: `value`, `expression`, `result`.

- The `value` represents the string that the rule has to search for.
- The `expression` represents the matching criteria: `equals`, `startsWith`, `endsWith`, `contains`
- The `result` represents the rule's output

#### Replace_Payee

This rule can be used to replace the name of a counterparty. This rule requires a look-up file named `payee.rules` located in the directory defined by the `rules.rules_folder` option of the config file.

Example: we want to add this transaction to the ledger, but we want to replace "Fresh Food Inc." with "FRESH FOOD".

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Add the `Replace_Payee` rule to the list of rules in the configuration file for the target financial institution and add this entry to the `payee.rules` file:

```
Fresh Food Inc.;equals;FRESH FOOD
```

#### Replace_Expense

This rule is used to assign an Account to a transaction based on the value of the `counterparty` index of the CSV file. This rule requires a look-up file named `account.rules` located in the directory defined by the `rules.rules_folder` option of the config file.

Example: we want to add this transaction to the ledger and we want to assing the Account `Expenses:Grocery` to the transaction.

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Add the `Replace_Expense` rule to the list of rules in the configuration file for the target financial institution and add this entry to the `account.rules` file:

```
Fresh Food Inc.;equals;Expenses:Groceries
```

#### Replace_Asset


### Custom rules

### Stage 1: move bank CSV file

Download a CSV bank file from your bank and move it to a staging area.
The script tries to find a file ending with `.csv` and starting with the provided String name and moves it to the target folder.
If more than one file is found matching the criteria, the operation is aborted.

Script to use: `bb_mover.py`

Arguments:

`-f`: configuration file

Examples:

```
./bb_mover.py -f ~/config/wells-fargo.yaml
```

### Stage 2: import the bank file into Beancount ledger

Import the data from the CSV file into the ledger.

Script to use: `bb_import.py`

Arguments:

### General options

`-f`: configuration file

`-v`: debug mode
