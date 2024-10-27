# Beanborg

Beanborg automatically imports financial transactions from external CSV files into the [Beancount](https://github.com/beancount/beancount) bookkeeping system. It is designed to streamline transaction importing by matching data to the correct expense accounts and doing so quickly, even with multiple files.

## Requirements

- Python 3
- Beancount v2

## Goals and key features

Beanborg has two main design goals:

- automatic matching of transaction data with the correct Expense accounts
- speed, capable of processing multiple financial CSV files in seconds.

Example:

Given the following transaction from a CSV file:

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Beanborg imports the transaction into Beancount and assigns the Account "Expense:Grocery" to the transaction:

```
2020-11-04 * "Fresh Food Inc." ""
csv: "04.11.2020,04.11.2020,Direct Debit,Fresh Food,-21,30,EUR,0000001,UK0000001444555"
md5: "60a54f6ed13ae7b7e70fd475eb677511"
Assets:Bank1:Bob:Current  -21.30 EUR
Expenses:Grocery      
```

## Additional features:

- Extendable rule-based system for transaction categorization.
- Duplicate transaction detection.
- Transaction classification using machine learning (ML) and large language models (LLM) (optional).
- Highly configurable with extensive rules.
- Smart archiving: files are renamed with start and end dates after processing.


## Installation

To install beanborg, use:

```
pip install git+https://github.com/luciano-fiandesio/beanborg.git
```

Fora specific branch:

```
pip install git+https://github.com/luciano-fiandesio/beanborg.git@BRANCH_NAME
```

## Workflow

Beanborg is based on a three-stage workflow:

1. Move the CSV file to the staging area.
2. Import the CSV into Beancount, categorizing transactions.
3. Archive the CSV after processing.

### Stage 1: Move Bank CSV File

Move a bank CSV file to the staging area:

```
bb_mover -f ~/config/wells-fargo.yaml
```

### Stage 2: Import the CSV into Beancount

Import the CSV into Beancount, categorizing transactions:

```
bb_import -f ~/config/wells-fargo.yaml
```

### Stage 3: Archive the CSV File
Move the CSV file to the archive folder:

```
bb_archive -f ~/config/wells-fargo.yaml
```

## Configuration

Each financial institution requires a dedicated YAML configuration file that defines the structure of the CSV file and the rules applied during import.

### Sample configuration file

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
    - ReplaceAsset
    - ReplaceExpense
```

### Structure of a configuration file

A Beanborg configuration must start with the `--- !Config` tag and has 3 main sections:

#### csv

The `csv` section of the configuration file determines the options related to the structure and location of the CVS file to import.
Here are the list of options for the `csv` section:

| Property           | Description                                                                                                                                                                                                                                             | Default | Example                        |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|--------------------------------|
| `download_path`    | Full path to the folder to which the CSV is downloaded to at the beginning of the import process. This option is only required by the `bb_mover` script.                                                                                                |         | "/home/john/download"          |
| name               | The name of the CSV file, at the time of download. Note that the name can be partial. For instance, is the CSV file is named "bank1-statement-03-2020", the `name` can be simply set to `bank1`. This option is only required by the `bb_mover` script. |         | `bank1`                        |
| `ref`              | Once the CVS file is imported into the staging area, it gets renamed using the value of `ref`. It is recommended to use a short string to identify the financial institution. This option is used by all the scripts.                                   |         | `com`                          |
| `separator`        | The field delimiter used in the financial institution's CSV file.                                                                                                                                                                                       | ,       |                                |
| `currency_sep`     | The decimal separator used in the CSV file                                                                                                                                                                                                              | .       |                                |
| `date_format`      | Date format used in the CVS file. The format is based on  strftime directives: https://strftime.org/. Note that the value must be in quotes                                                                                                             |         | "%d/%m/%Y"                     |
| `skip`             | Number of lines of the CSV file to skip during import                                                                                                                                                                                                   | 1       |                                |
| `target`           | The folder name or path in which the CSV file is moved to during the first stage.    s                                                                                                                                                                  | tmp     |                                |
| `archive`          | The folder name of path in which the CSV file is archived during the archive stage                                                                                                                                                                      | archive |                                |
| `post_move_script` | Path to a post-move script that is executed after the CSV file is moved into the work folder. The script must use a `shebang` (e.g. `#!/bin/bash`) in order to be executed.                                                                             |         | `/home/tom/scripts/convert.sh` |
| keep_original      | Keep the CSV file from the `download_path`. The default is to delete it after the move process. This option is only required by the `bb_mover` script.                                                                                                  | `False` | `True`                         |

#### indexes

The `indexes` section of the configuration file allows mapping each CSV "column" (or index) to the information required to parse and import the data. In other words, each option is used by Beanborg to determine where the `date` or `amount` of each transaction is located on the CVS file.

Note that the first index starts from `0`.

| Property       | Description                                                                                                                                                                   | Default |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| `date`         | The index corresponding to the date of the transaction.                                                                                                                       | 0       |
| `counterparty` | The index corresponding to the name of the counterparty of the transaction.                                                                                                   | 3       |
| `amount`       | The index corresponding to the amount of the transaction (debit or credit).                                                                                                   | 4       |
| `account`      | The index corresponding to the account of the transaction (e.g. the IBAN or ABA code).                                                                                        | 4       |
| `currency`     | The index corresponding to the currency of the transaction.                                                                                                                   | 5       |
| `tx_type`      | The index corresponding to the transaction type.                                                                                                                              | 2       |
| `amount_in`    | Some financial institutions, use separate indexes for debit and credit. In this case, it is possible to specify the index for the index corresponding to the credited amount. |         |
| `narration`    | The index corresponding to the narration or reference field of the transaction.                                                                                               |         |

#### rules

| Property                       | Description                                                                                                                | Default            |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------|--------------------|
| `beancount_file`               | The master Beancount ledger file. This property is mandatory and it is required to by the duplication detection mechanism. | `main.ldg`         |
| `rules_folder`                 | The folder name in which custom rules and look-up tables files are stored                                                  | `rules`            |
| `account`                      | This property is normally used when a CSV file doesn't contain any account property (IBAN, ABA, account number, etc).      |                    |
| `currency`                     | Force a default currency                                                                                                   |                    |
| `default_expense`              | Default expense account                                                                                                    | `Expenses:Unknown` |
| `force_negative`               | TODO                                                                                                                       | False              |
| `invert_negative`              | TODO                                                                                                                       | False              |
| `origin_account`               | Specifies the origin account of each transaction                                                                           |                    |
| `ruleset`                      | List of rules to apply to the CSV file. See `rules` section.                                                               |                    |
| `advanced_duplicate_detection` | Enable the advanced duplication detection rule (see Advanced Duplicate Detection section)                                  | `true`             |

## Rules

Beanborg’s rules engine is highly customizable, allowing users to automate the categorization of transactions based on pre-existing rules. 
Each rule is referenced by name and can be used for tasks such as assigning accounts, ignoring transactions, or modifying transaction details like the counterparty's name.

Some rules rely on **lookup tables**, which are semicolon-separated CSV files. These files contain three columns: `value`, `expression`, and `result`, allowing flexible criteria for matching and transforming data.

- **value**: The string that the rule searches for.
- **expression**: The matching criteria used by the rule, such as `equals`, `equals_ic`, `startsWith`, `endsWith`, `contains`, or `contains_ic`.
  - `equals_ic` and `contains_ic` are case-insensitive versions of `equals` and `contains`.
- **result**: The output of the rule when a match is found.

### Example: Expense Categorization Rule

For instance, if you want to categorize any transaction where the payee is "Walmart" under `Expenses:Groceries`, the lookup entry would be:

`Walmart;equals;Expenses:Groceries`


To ensure that any variation of "Walmart," regardless of case, is also matched, you can use:

`Walmart;contains_ic;Expenses:Groceries`

The `_ic` indicates `ignore case`.

The following sections provide a detailed explanation of the rules available in Beanborg.

#### ReplacePayee

The `ReplacePayee` rule is used to modify the name of a transaction’s counterparty. This is useful when you want to standardize or adjust the names in your financial records.

This rule requires a lookup file named `payee.rules`, which should be placed in the directory defined by the `rules.rules_folder` option in the configuration file.

Suppose you want to modify a transaction where the counterparty is listed as "Fresh Food Inc." and replace it with "FRESH FOOD" when importing the data into the ledger.

Given the following CSV transaction:

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

You would follow these steps:

1. Add the `ReplacePayee` rule to the list of rules in the configuration file for the relevant financial institution.
2. In the `payee.rules` lookup file, add the following entry:

```
Fresh Food Inc.;equals;FRESH FOOD
```

This will ensure that the counterparty "Fresh Food Inc." is replaced with "FRESH FOOD" in your Beancount ledger.


#### ReplaceExpense

The `ReplaceExpense` rule is used to assign an account to a transaction based on the value of the `counterparty` index from the CSV file. This rule is particularly helpful for categorizing transactions into the appropriate expense accounts.

This rule requires a lookup file named `account.rules`, which should be located in the directory defined by the `rules.rules_folder` option in the configuration file.

Suppose you want to categorize a transaction where the counterparty is "Fresh Food Inc." under the account `Expenses:Grocery` when importing the data into Beancount.

Given the following CSV transaction:

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

You would follow these steps:

1. Add the `ReplaceExpense` rule to the list of rules in the configuration file for the relevant financial institution.
2. In the `account.rules` lookup file, add the following entry:

```
Fresh Food Inc.;equals;Expenses:Groceries
```

This will ensure that any transaction with "Fresh Food Inc." as the counterparty will be assigned to the `Expenses:Grocery` account in your Beancount ledger.


#### ReplaceAsset


The `ReplaceAsset` rule assigns an "origin" account to a transaction based on the value of the `account` index in a CSV file. 
This rule is useful for ensuring that transactions are recorded with the correct source account in Beancount.

The `ReplaceAsset` rule is automatically added to the ruleset, even if it is not explicitly declared in the configuration file.

##### Origin Account Resolution

The rule can resolve the origin account in two ways:

1. Using a lookup file named `asset.rules`, located in the directory defined by the `rules.rules_folder` option in the config file.
2. Using the `rules.origin_account` property specified directly in the configuration file.

Suppose you want to import the following CSV transaction and assign the origin account as `Assets:Jim:Current`:

```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

##### Steps:

1. Create an `asset.rules` lookup file and add the following entry:

```
value;expression;result 
UK0000001444555;equals;Assets:Jim:Current
```

This entry will match the `account` index value (`UK0000001444555`) and assign the origin account as `Assets:Jim:Current` in your Beancount ledger. 
If no match is found, the rule will default to `Assets:Unknown`.

#### Handling Missing `account` Index

If the CSV file does not contain an `account` index, you can specify the account directly in the configuration file by using the `account` property:

```yaml
--- !Config
...
rules:
  account: UK0000001444555
```

This will assign the account `Assets:Jim:Current` to all transactions in the CSV file, regardless of the actual account value in the CSV.

Alternatively, you can set the `origin_account` property in the `rules` block and skip this rule completely.

```yaml
--- !Config
...
rules:
  origin_account: Assets:Jim:Current
```

#### SetAccounts

Assigns an "origin" account to a transaction, based on value of the `account` index of a CSV file row.
This rule is useful to assign the correct source account of a CSV transaction. This rule is **implicitly added** to the ruleset, even if it doesn't get declared
    
The rule can resolve the origin account in two ways: 

- using a look-up file named `asset.rules` located in the directory defined by the `rules.rules_folder` option of the config file
- using the value of the property `rules.origin_account` of the config file in use

As an example, let's take this CSV transaction. We want to import the transaction so that the origin account is set to `Assets:Jim:Current`.
 
```
04.11.2020;04.11.2020;Direct Debit;"Fresh Food Inc.";-21,30;EUR;0000001;UK0000001444555
```

Add the `ReplaceAsset` to the `ruleset` and create an `asset.rules` file. Add the following snippet to the `asset.rules` file:

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

#### SetAccounts

The `SetAccounts` sets both  the **origin** and **destination** account for a given transaction, based on one or more values of a given CSV index.
This rule is useful for transactions like ATM withdrawals, where both accounts need to be defined.

As an example, consider the following CSV transaction representing an ATM withdrawal:

```
01.12.2020;01.11.2020;Cash Withdrawal;Bank Of Holland;-100;EUR;0000001;UK0000001444555
```

In this case, we want to set the **origin** account to `Assets:Jim:Current` and the **destination** account to `Assets:Jim:Cash`.

The `Set_Accounts` rule can be configured as follows:

```
- name: Set_Accounts
  from: Assets:Jim:Current
  to: Assets:Jim:Cash
  csv_index: 2
  csv_values: Cash Withdrawal
```


- The rule points to `csv_index: 2`, which refers to the third column in the CSV (indexing starts from 0).
- If the value at index 2 matches `Cash Withdrawal`, the origin account is set to `Assets:Jim:Current` and the destination account is set to `Assets:Jim:Cash`.

The `Set_Accounts` rule supports multiple `csv_values` separated by a semicolon (`;`). 
If any of the specified values match, the rule is applied. 
For example, if you want the rule to apply to different forms of "withdrawal" in multiple languages:


```
- name: SetAccounts
      from: Assets:Jim:Current
      to: Assets:Jim:Cash
      csv_index: 2
      csv_values: Cash Withdrawal;*Retiro*;*Ritiro*
```

- The `csv_values` are case-insensitive.
- Wildcards are supported using `fnmatch`. In the example above, 
the wildcard * is used to match any string that contains `Retiro` or `Ritiro`.

#### IgnoreByPayee

The `IgnoreByPayee` rule can be used to ignore transactions based on the value of the `counterparty` index in a CSV file. 
This is useful when you want to exclude specific transactions from being imported into the ledger.


Suppose you want to ignore any transactions where the counterparty is "Mc Donald" or "Best Shoes". You can configure the rule as follows:

```
- name: IgnoreByPayee
      ignore_payee:
        - Mc Donald
        - Best Shoes
```

The names of counterparties in the `ignore_payee` list are case-insensitive. This means both "Mc Donald" and "mc donald" would be matched and ignored.


#### IgnoreByStringAtPos

The `IgnoreByStringAtPos` rule allows you to ignore a transaction based on the value found at a specific index in the CSV file. This is useful for filtering out transactions that meet specific criteria in a particular column.

### Example

To ignore transactions where the value in index 4 (fifth column) matches `abc0102`, configure the rule like this:

```yaml
- name: IgnoreByStringAtPos
  ignore_string_at_pos: 
    - abc0102;4
```
- The index in the CSV file starts from `0`, so `4` refers to the fifth column.
- The values specified in `ignore_string_at_pos` are case-insensitive, meaning `abc0102` and `ABC0102` would both be matched and ignored.




### Custom rules

TODO

### Advanced Duplicate Detection

Beanborg employs a simple duplicate detection method. When a transaction is imported into the ledger, the transaction CSV data are hashed and the hash is permanently associated
to the ledger entry (using [transaction metadata](https://beancount.github.io/docs/beancount_language_syntax.html#metadata)).

Beanborg includes a robust duplicate detection mechanism to prevent importing the same transaction multiple times. This method works by hashing the transaction data from the CSV file and associating the resulting hash with the ledger entry using [transaction metadata](https://beancount.github.io/docs/beancount_language_syntax.html#metadata).


#### Basic Duplicate Detection

When a transaction is imported, Beanborg generates a hash of the CSV data. For example, consider the following CSV entry:

```
2019-03-17,2019-03-18,Überweisung,nick sammy,-520,00,IT389328932723787832,Personal,E-d3be986080315683eee5efbeb297243a,Gebucht,Privat
```


The corresponding hash (`2454abe7257b2b40dfa9e5d24b6e16e7`) is stored in the ledger's metadata under the `md5` key. 
If you attempt to import the same CSV row again, Beanborg detects that the hash already exists and rejects the transaction, preventing duplicates.

#### Handling Inconsistent Data

In practice, banks may modify transaction details in the CSV file after the first export. For example, consider the following modified entry:

```
2019-03-17,2019-03-18,Überweisung,Nick Sammy,-520,00,IT389328932723787832,Personal,E-d3be986080315683eee5efbeb297243a,Gebucht,Privat
```

In this case, the payee’s name has changed from `nick sammy` to `Nick Sammy`. Since this small variation alters the transaction's hash, Beanborg would treat it as a different entry, bypassing the basic duplicate detection mechanism.

To address these inconsistencies, Beanborg implements a secondary, advanced duplicate detection system. In addition to hashing the transaction, it checks if a transaction with the **same date and amount** already exists in the ledger for the current account. If a potential duplicate is found, Beanborg prompts the user to confirm whether the transaction should be imported.

The advanced duplicate detection can be disabled by setting the `advanced_duplicate_detection` option to `false` in the account’s configuration file, allowing Beanborg to rely solely on hash-based detection.

```yaml
rules:
  advanced_duplicate_detection: false
```

### Machine Learning-Based Transaction Categorization

Beanborg integrates an advanced Machine Learning (ML) mechanism to automatically categorize transactions when rule-based categorization is not possible. This system ensures that transactions are accurately classified by leveraging both machine learning and, optionally, the ChatGPT API.


#### How It Works

When Beanborg is unable to categorize a transaction through its predefined rules, it invokes an ML model trained on historical data to predict the most likely categories. This provides an additional layer of automation to reduce the need for manual intervention.

- **Top Predictions**: The system generates up to three category predictions using the ML model. These predictions are displayed to the user, who can select one of the suggested categories or manually assign a category if none of the suggestions are appropriate.
  
- **Optional GPT Integration**: If enabled, a fourth prediction is provided by querying the ChatGPT API, offering an AI-based suggestion that complements the ML model's predictions.

#### Prediction Workflow

The categorization workflow follows a structured process:

1. **Transaction Evaluation**: If no rule matches a transaction, Beanborg invokes the ML model to generate category predictions.
2. **Top 3 ML Predictions**: The system displays the three most likely categories for the transaction based on the training dataset and the features extracted.
3. **User Interaction**: The user can choose one of the three ML-generated categories or manually assign a category if the predictions are not suitable.
4. **Optional GPT Suggestion**: If enabled, a fourth prediction generated by the ChatGPT API is displayed, offering an alternative suggestion.
5. **Dynamic Learning**: The system updates the training dataset based on the user's final choice, enabling continuous model improvement.

#### Enabling the ChatGPT API predictions

To enable the optional ChatGPT API-based prediction, follow these steps:

1. Set the `OPENAI_API_KEY` environment variable with your OpenAI API key.
2. Update the configuration file to activate the feature by setting the `rules.use_llm` property to `true`.

Your configuration should look like this:

```yaml
rules:
  use_llm: true
```

With these settings enabled, Beanborg will include an additional category prediction generated by the ChatGPT API alongside the machine learning model’s top predictions.

