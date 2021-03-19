# BEANBORG

Helper scripts for quick Plain Text Accounting using [Beancount](http://furius.ca/beancount/).

## Requirements

- Python 3
- Beancount

## Goals

The main goal of this set of scripts is to import financial transactions from a financial institution's CSV file into the Beancount ledger and automatically assign the correct Expense account to the transaction.

For instance, given the following CSV entry:

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food";-21,30;EUR;0000001;UK0000001444555
```

will be imported by assigning the Account "Expense:Grocery" to the transaction:

```
2020-11-04 * "Fresh Food" ""
csv: "04.11.2020,04.11.2020,Direct Debit,Fresh Food,-21,30,EUR,0000001,UK0000001444555"
md5: "60a54f6ed13ae7b7e70fd475eb677511"
Assets:Bank1:Bob:Current  -21.30 EUR
Expenses:Grocery      
```

The automatic categorization is rule-based. The scripts come with a set of standard rules, but it is possible to dynamically invoke custom rules.

## Workflow

This set of scripts is based on a very specific workflow, which may or may not work for you.

The workflow is based on 3 distinct stages:

- Move a downloaded bank CSV file into the stage area
- Import the CSV file into Beancount ledger and automatically categorize the transactions
- Move the bank CSV file into archive area

### Configuration

Each financial institution from which data will be imported, must have a dedicated yaml configuration file.
The configuration file is used by the import scripts to determine the CSV file structure and other information.

### Structure of a configuration file

A Beanborg configuration must start with `--- !Config` and has 3 sections:

#### csv

This section of the configuration file determines the options related to the structure and localtion of the CVS file.
These are the list of options for the `csv` section:

| Property      | Description                                                                                                                                                                                      | Default | Example             |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|---------------------|
| download_path | Full path to the folder to which the CSV is downloaded to                                                                                                                                        |         | /home/john/download |
| name          | The name of the CSV file, at the time of download. Note that the name can be partial. For instance, is the CSV file is named "bank1-statement-03-2020", the `name` can be simply set to `bank1`  |         | `bank1`             |
| ref           | Once the CVS file is imported into the staging area, it gets renamed using the value of `ref`. It is recommended to use a short string to identify the financial institution                    |         | `com`               |
| separator     | The CSV separator                                                                                                                                                                                | ,       |                     |
| currency_sep  | The decimal separator used in the CSV file                                                                                                                                                       | .       |                     |
| date_format   | Date format used in the CVS file. The format is based on  strftime directives: https://strftime.org/. Note that the value must be in quotes                                                      |         | "%d/%m/%Y"          |
| skip          | CSV file lines to skip during import                                                                                                                                                             | 1       |                     |
| target        | The folder name or path in which the CSV file is moved to during the first stage.                                                                                                                | tmp     |                     |
| archive       | The folder name of path in which the CSV file is archived during the archive stage                                                                                                               | archive |                     |

#### indexes

The `indexes` section of the configuration file allows to configure how to map each CSV "column" (or index) to the information required to parse and import the data. In other words, each option is used by Beanborg to determine where the `date` or `amount` of each transaction is located on the CVS file.

Note that the first index starts from `0`.

| Property     | Description                                                                                                                                                                                      | Default |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| date         | The index corresponding to the date of the transaction                                                                                                                                           | 0       |
| counterparty | The index corresponding to the name of the counterparty of the transaction                                                                                                                       | 3       |
| amount       | The index corresponding to the amount of the transaction (either debit or credit)                                                                                                                | 4       |
| currency     | The index corresponding to the currency of the transaction                                                                                                                                       | 5       |
| tx_type      | The index corresponding to the transaction type                                                                                                                                                  | 2       |
| amount_in    | Some financial institutions, use separate indexes for debit and credit. In this case, it is possible to specify the index for the  index corresponding to the credited amount of the transaction |         |


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


### Stage 1: move bank file

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
