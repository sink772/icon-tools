# ICON Tools

A collection of CLI commands to perform the following actions.
  * Check governance status of given network
  * Query and transfer your ICX
  * Query and claim your IScore
  * Query and set staking
  * Query and set delegations

## Usage

```bash
(.venv) $ ./run.py -h
usage: run.py [-h] [-e ENDPOINT] [-k KEYSTORE] [-p PASSWORD] command ...

optional arguments:
  -h, --help            show this help message and exit
  -e ENDPOINT, --endpoint ENDPOINT
                        an endpoint for connection
  -k KEYSTORE, --keystore KEYSTORE
                        keystore file for creating transactions
  -p PASSWORD, --password PASSWORD
                        password for the keystore file

Available commands:
  command
    gov                 Check governance status
    balance             Get ICX balance of given address
    transfer            Transfer ICX to the given address
    iscore              Query and claim IScore
    stake               Query and set staking
    delegate            Query and set delegations
```

## Auto-staking

You can perform the auto-staking operation (claim your IScore, set new stake amount, and set new delegations)
without user intervention through the following command line.

```bash
(.venv) $ ./run.py -k <your_keystore> stake --set --auto
```
