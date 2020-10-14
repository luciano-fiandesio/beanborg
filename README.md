# BEANBORG

Helper scripts for quick Plain Text Accounting using [Beancount](http://furius.ca/beancount/).

## Requirements

- Python 3
- Beancount

## Rationale and general structure



## Workflow

This set of scripts is based on a very specific workflow, which may or may not work for you.
The workflow is based on 3 distinct stages:

- Move bank CSV file into stage area
- Import CSV file into Beancount ledger and categorize the transactions
- Move bank CSV file into archive area

### Stage 1: move bank file

Download a CSV bank file from your bank and move it to a staging area.
The script tries to find a file ending with `.csv` and starting with the provided String name and moves it to the target folder.
If more than one file is found matching the criteria, the operation is aborted.

Script to use: `bb-mover.py`

Arguments:

`-d`: directory to scan for incoming CVS bank files
`-f`: a String for which the file to import starts with
`-t`: the folder name or path in which the bank file is moved
`-b`: the bank identification string used in the following stages


Examples:

```
./bb-mover.py -d ~/Downloads/ -f 'Umsaetze_' -t tmp -b 'cb'
```

Moves a file that starts with `Umsaetze_` and ends with `csv` into the target folder `tmp`. Renames the file to `cb.csv`.

```
./bb-mover.py -d ~/Downloads/ -f 'Revolut' -t /tmp/revolut -b 'rev'
```

Moves a file that starts with `Revolut` and ends with `csv` into the target folder `/tmp/revolut`. Renames the file to `rev.csv`.

### Stage 2: import the bank file into Beancount ledger

Import the data from the CSV file into the ledger.

Script to use: `bb-import.py`

Arguments:

General options

`-f`: path to the csv file to import
`-b`: target Beancount file
`-s`: separator used in the CSV file. Default: `,`
`-l`: CSV file lines to skip during import. Default: `1`
`-o`: Date format used in the CVS file. The format is based on `strftime` directives: https://strftime.org/
`-t`: Currency decimal separator. Default: `.`

CSV file index options

`-d`: CSV file index for the date column. Default: `0`
`-p`: CSV file index for the payee column. Default: `3`
`-m`: CSV file index for the amount column. Default: `4`
`-i`: CSV file index for the account identification column. Default: `8`
`-c`: CSV file index for the currency identification column. Default: `5`
`-x`: CSV file index for the transaction type column. Default: `2`


Rule options

`-r`: path to the rules folder. Default: `rules`
`-z`: name of the rule file to use for the import
`-k`: Default expense category. Default: `Expenses:Unknown`

Other options

`-a`: account identification string, in case the CSV file does't have it 
`-u`: force currency string during import 
`-v`: print debug info
`-q`: CSV file index for amount "in" -- TODO
`-g`: force negative -- TODO
`-e`: invert negative -- TODO



## Sample data

move: `../beanborg/bb-mover.py -d ~/tmp/ -f 'bank1' -t 'tmp' -b 'b1'`

import  `../beanborg/bb-import.py -f tmp/b1.csv -b 'main.ldg' -r 'myrules' -z 'bank1.rules' -i 7 -t ',' -s ';' -o '%d.%m.%Y' -v`









