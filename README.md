Beanborg automatically imports financial transactions from external CSV files into the [Beancount](http://furius.ca/beancount/) bookkeeping system.

## Requirements

- Python 3
- Beancount v2

## Goals and key features

Beanborg has two main design goals:

- automatic matching of transaction data with the correct Expense accounts
- speed, the tool is designed to process several financial CSV files in few seconds

Given the following transaction from a CSV file:

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Beanborg imports the transaction in Beancount and assign the Account "Expense:Grocery" to the transaction:

```
2020-11-04 * "Fresh Food Inc." ""
csv: "04.11.2020,04.11.2020,Direct Debit,Fresh Food,-21,30,EUR,0000001,UK0000001444555"
md5: "60a54f6ed13ae7b7e70fd475eb677511"
Assets:Bank1:Bob:Current  -21.30 EUR
Expenses:Grocery      
```

Other features:

- sophisticated and extendible rule based system
- duplicated transactions detection 
- highly configurable
- smart archiving function: when archiving a CSV file, the file is renamed using the start and end date of the CSV file

## Tutorial

A simple tutorial is available [here](https://github.com/luciano-fiandesio/beanborg/blob/master/tutorial/README.md)

## Installation

```
pip install git+https://github.com/luciano-fiandesio/beanborg.git
```

If you want to install from a specific branch:

```
pip install git+https://github.com/luciano-fiandesio/beanborg.git@BRANCH_NAME
```


## Workflow

Beanborg is based on a very specific workflow, which may or may not work for you.

The workflow is based on 3 distinct stages:

- Move a CSV file downloaded from a bank/financial institution website into the stage area
- Import the CSV file into the Beancount ledger and automatically categorize the transactions
- Move the bank CSV file into the archive area

The first stage is executed by the `bb_mover.py` script.

The second stage is executed by the `bb_import.py` script.

The third stage is executed by the `bb_archive.py` script.

### Configuration

Each financial institution from which data will be imported must have a dedicated YAML configuration file.
The configuration file is used by the import scripts to determine the CSV file structure and other information, including which rules to apply.

### Structure of a configuration file

A Beanborg configuration must start with the `--- !Config` tag and has 3 main sections:

#### csv

The `csv` section of the configuration file determines the options related to the structure and location of the CVS file to import.
Here are the list of options for the `csv` section:

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
| post_move_script       | Path to a post-move script that is executed after the CSV file is moved into the work folder. The script must use a `shebang` (e.g. `#!/bin/bash`) in order to be executed.|  |`/home/tom/scripts/convert.sh` |
| keep_original       | Keep the CSV file from the `download_path`. The default is to delete it after the move process. This option is only required by the `bb_mover` script.|`False`|`True` |

#### indexes

The `indexes` section of the configuration file allows mapping each CSV "column" (or index) to the information required to parse and import the data. In other words, each option is used by Beanborg to determine where the `date` or `amount` of each transaction is located on the CVS file.

Note that the first index starts from `0`.

| Property     | Description                                                                             | Default |    
|--------------|-----------------------------------------------------------------------------------------|---------|
| date         | The index corresponding to the date of the transaction                                  |    0    |
| counterparty | The index corresponding to the name of the counterparty of the transaction              |    3    |
| amount       | The index corresponding to the amount of the transaction (debit or credit)              |    4    |
| account      | The index corresponding to the account of the transaction (e.g. the IBAN or ABA code)   |    4    |
| currency     | The index corresponding to the currency of the transaction                              |    5    |
| tx_type      | The index corresponding to the transaction type                                         |    2    |
| amount_in    | Some financial institutions, use separate indexes for debit and credit. In this case, it is possible to specify the index for the index corresponding to the credited amount  |         |
| narration    | The index corresponding to the narration or reference field of the transaction          |         |                                                                                   


#### rules

| Property                             | Description                                                                                                                | Default            |
|-----------------                     |----------------------------------------------------------------------------------------------------------------------------|--------------------|
| beancount_file                       | The master Beancount ledger file. This property is mandatory and it is required to by the duplication detection mechanism. | `main.ldg`         |
| rules_folder                         | The folder name in which custom rules and look-up tables files are stored                                                  | `rules`            |
| account                              | This property is normally used when a CSV file doesn't contain any account property (IBAN, ABA, account number, etc).      |                    |
| currency                             | Force a default currency                                                                                                   |                    |
| default_expense                      | Default expense account                                                                                                    | `Expenses:Unknown` |
| force_negative                       | TODO                                                                                                                       | False              |
| invert_negative                      | TODO                                                                                                                       | False              |
| origin_account                       | Specifies the origin account of each transaction                                                                           |                    |
| ruleset                              | List of rules to apply to the CSV file. See `rules` section.                                                               |                    |
| advanced_duplicate_detection         | Enable the advanced duplication detection rule (see Advanced Duplicate Detection section)                                  | `true`             |

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
  ruleset:
    - Replace_Asset
    - Replace_Expense
```

### Rules

The Beanborg's rules engine comes with a number of preexisting rules. 
Rules are always referenced by **name** and can be used to assign an account to a transaction, ignore a transaction or replace the name of a transaction's counterparty.
Some rules require a look-up table file to find the right value and execute the rule action.

Look-up table files are semicolon-separated CSV files, composed of 3 columns: `value`, `expression`, `result`.

- The `value` represents the string that the rule has to search for.
- The `expression` represents the matching criteria: `equals`, `equals_ic` `startsWith`, `endsWith`, `contains`, `contains_ic`
- The `result` represents the rule's output

As an example, let's consider a look-up rule that has to set the expense category to `Expenses:Groceries`, whenever the payee contains the word `Walmart`.
The look-up entry will look like:

`Walmart;equals;Expenses:Groceries`

If we want to make sure that the `Expenses:Groceries` categories is selected whenever the word `Walmart` appears in the payee reference, regardless of the case, we can use:

`Walmart;contains_ic;Expenses:Groceries`

The `_ic` indicates `ignore case`.


The next section lists the rules which are available in Beanborg.

#### Replace_Payee

This rule can be used to replace the name of a counterparty. This rule requires a look-up file named `payee.rules` located in the directory defined by the `rules.rules_folder` option of the config file.

For example: we want to add this transaction to the ledger, but we want to replace "Fresh Food Inc." with "FRESH FOOD".

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Add the `Replace_Payee` rule to the list of rules in the configuration file for the target financial institution and add this entry to the `payee.rules` file:

```
Fresh Food Inc.;equals;FRESH FOOD
```

#### Replace_Expense

This rule is used to assign an Account to a transaction based on the value of the `counterparty` index of the CSV file. This rule requires a look-up file named `account.rules` located in the directory defined by the `rules.rules_folder` option of the config file.

For example: we want to add this transaction to the ledger and we want to assign the Account `Expenses:Grocery` to the transaction.

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Add the `Replace_Expense` rule to the list of rules in the configuration file for the target financial institution and add this entry to the `account.rules` file:

```
Fresh Food Inc.;equals;Expenses:Groceries
```

#### Replace_Asset

Assigns an "origin" account to a transaction, based on value of the `account` index of a CSV file row.
This rule is useful to assign the correct source account of a CSV transaction. This rule is **implicitly added** to the ruleset, even if it doesn't get declared
    
The rule can resolve the origin account in two ways: 

- using a look-up file named `asset.rules` located in the directory defined by the `rules.rules_folder` option of the config file
- using the value of the property `rules.origin_account` of the config file in use

As an example, let's take this CSV transaction. We want to import the transaction so that the origin account is set to `Assets:Jim:Current`.
 
```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Add the `Replace_Asset` to the `ruleset` and create an `asset.rules` file. Add the following snippet to the `asset.rules` file:

```
value;expression;result
UK0000001444555;equals;Assets:Jim:Current
```

The rule will match the value of the `account` CSV index (`UK0000001444555`) to `Assets:Jim:Current` and create the Beancount transaction. If no match is found, the rule will default to `Assets:Unknown`.

In a scenario where a CSV file does not contain any `account` index, it is possible to specify the account value by setting the `account` property in the config file in use.

```
--- !Config
...
rules:
  account: UK0000001444555
```

Note that in the majority of situations, it is more intuitive to set the `origin_account` property on the `rules` block and skip this rule completely.

```
--- !Config
...
rules:
  origin_account: Assets:Jim:Current
```

#### Set_Accounts

This rule does set the origin and destination account for a given transaction, based on one or more values of a given CSV index.

As an example, let's take this CSV transaction - an ATM withdrawal from a bank.

```
01.12.2020;01.11.2020;Cash Withdrawal;Bank Of Holland;-100;EUR;0000001;UK0000001444555
```

When such a transaction is imported, we would like to set the origin account to `Assets:Jim:Current` and the destination account to `Assets:Jim:Cash`.

This is how the `Set_Accounts` rule can help:

```
- name: Set_Accounts
  from: Assets:Jim:Current
  to: Assets:Jim:Cash
  csv_index: 2
  csv_values: Cash Withdrawal
```

With the above rule configuration, we are pointing the rule to the index `2` (remember index count starts at `0`) and if the value of the index matches `Cash Withdrawal`,
then the origin and destination accounts are set on the Beancount transaction. This rule supports multiple `csv_values`, separated by `;`. If any of the values matches, the rule is applied:

The CSV values are **case-insensitive** and support wildcard matching using `fnmatch`.

```
- name: Set_Accounts
      from: Assets:Jim:Current
      to: Assets:Jim:Cash
      csv_index: 2
      csv_values: Cash Withdrawal;*Retiro*;*Ritiro*
```

#### Ignore_By_Payee

This rule can be used to ignore a transaction based on the value of the `counterparty` index.

```
- name: Ignore_By_Payee
      ignore_payee:
        - Mc Donald
        - Best Shoes
```
The counterparty names are **case-insensitive**.

#### Ignore_By_StringAtPos

This rule can be used to ignore a transaction based on the value of a specific CVS index.

```
- name: Ignore_By_StringAtPos
      ignore_string_at_pos: 
        - abc0102;4
```

The values are **case-insensitive**.

### Custom rules

TODO

### Advanced Duplicate Detection

Beanborg employs a simple duplicate detection method. When a transaction is imported into the ledger, the transaction CSV data are hashed and the hash is permanently associated
to the ledger entry (using [transaction metadata](https://beancount.github.io/docs/beancount_language_syntax.html#metadata)).

For instance, given this CSV entry:

`2019-03-17,2019-03-18,Überweisung,nick sammy,-520,00,IT389328932723787832,Personal,E-d3be986080315683eee5efbeb297243a,Gebucht,Privat`

The corresponding hash (`2454abe7257b2b40dfa9e5d24b6e16e7`) is attached to the ledger's entry using the `md5` key metadata.
If we try to import the same CSV row again, the hash will collide and the transaction is rejected.

Unfortunately, there are cases where a bank (hello German banks!) may change the data within a CSV entry after few days from the first CSV export. 
So the above CSV entry can change to:

`2019-03-17,2019-03-18,Überweisung,Nick Sammy,-520,00,IT389328932723787832,Personal,E-d3be986080315683eee5efbeb297243a,Gebucht,Privat`

Can you spot the difference? 
The name of the payee has changed from `nick sammy` to `Nick Sammy`.
This throws a wrench into the wheels of the duplicate detection algorithm, because the hash of the second entry differs from the hash of the first entry.
So, if we import this transaction again, it will not be detected as duplicated and imported into the ledger.

To solve this problem, a secondary detection algorithm has been introduced. 
When Beanborg imports a transaction from the CSV file, it checks if an existing transaction having the same 
date and amount already exists in the ledger for the current account file. 
If a transaction is found in the ledger, Beanborg ask the user to confirm the import of the suspicious transaction.
This feature can be switched off setting `advanced_duplicate_detection` to `false` in the account's configuration file.
 
### Stage 1: move bank CSV file

Download a CSV bank file from your bank and move it to a staging area.
The script tries to find a file ending with `.csv` and starting with the provided String name and moves it to the target folder.
If more than one file is found matching the criteria, the operation is aborted.

Script to use: `bb_mover.py`

Arguments:

`-f`: configuration file

Examples:

```
bb_mover.py -f ~/config/wells-fargo.yaml
```

### Stage 2: import the bank file into Beancount ledger

Import the data from the CSV file into the ledger.

Script to use: `bb_import.py`

Arguments:

`-f`: configuration file

Examples:

```
bb_import.py -f ~/config/wells-fargo.yaml
```

### Stage 3: archive the CSV file

Move the downloaded CSV file into an `archive` folder.

Script to use: `bb_archive.py`

Arguments:

`-f`: configuration file

Examples:

```
bb_archive.py -f ~/config/wells-fargo.yaml
```
