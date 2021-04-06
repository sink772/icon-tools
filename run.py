#!/usr/bin/env python

import argparse

from icx import icx
from iiss import iscore, stake, delegate, prep
from score import gov


def address_type(string):
    if isinstance(string, str) and len(string) == 42:
        prefix = string[:2]
        if prefix == "hx" or prefix == "cx":
            body_bytes = bytes.fromhex(string[2:])
            body = body_bytes.hex()
            if str(string) == prefix + body:
                return string
    raise argparse.ArgumentTypeError(f"Invalid address: '{string}'")


def tx_hash_type(string):
    if isinstance(string, str) and len(string) == 66:
        prefix = string[:2]
        if prefix == "0x":
            hash_bytes = bytes.fromhex(string[2:])
            tx_hash = hash_bytes.hex()
            if str(string) == prefix + tx_hash:
                return string
    raise argparse.ArgumentTypeError(f"Invalid txHash: '{string}'")


class Command(object):

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-e', '--endpoint', type=str, default="mainnet", help='an endpoint for connection')
        parser.add_argument('-k', '--keystore', type=argparse.FileType('r'),
                            help='keystore file for creating transactions')
        parser.add_argument('-p', '--password', type=str, help='password for the keystore file')

        subparsers = parser.add_subparsers(title='Available commands', metavar='command')
        subparsers.required = True
        subparsers.dest = 'command'

        # create a parser for 'gov' command
        gov_parser = subparsers.add_parser('gov', help='Check governance status')
        gov_parser.add_argument('--accept-score', type=tx_hash_type, metavar='TX_HASH',
                                help='accept the given deploy transaction')
        gov_parser.add_argument('--reject-score', type=tx_hash_type, metavar='TX_HASH',
                                help='reject the given deploy transaction')
        gov_parser.add_argument('--reason', type=str, help='reason for rejecting')

        # create a parser for 'balance' command
        balance_parser = subparsers.add_parser('balance', help='Get ICX balance of given address')
        balance_parser.add_argument('--address', type=address_type, help='target address to perform operations')
        balance_parser.add_argument('--all', action='store_true', help='include the staked ICX')

        # create a parser for 'transfer' command
        balance_parser = subparsers.add_parser('transfer', help='Transfer ICX to the given address')
        balance_parser.add_argument('--to', type=address_type, required=True, help='the recipient address')
        balance_parser.add_argument('--amount', type=int, help='the amount of ICX (in loop)')

        # create a parser for 'iscore' command
        iscore_parser = subparsers.add_parser('iscore', help='Query and claim IScore')
        iscore_parser.add_argument('--address', type=address_type, help='target address to perform operations')
        iscore_parser.add_argument('--claim', action='store_true', help='claim the reward that has been received')

        # create a parser for 'stake' command
        stake_parser = subparsers.add_parser('stake', help='Query and set staking')
        stake_parser.add_argument('--address', type=address_type, help='target address to perform operations')
        stake_parser.add_argument('--set', action='store_true', help='set new staking amount')
        stake_parser.add_argument('--auto', action='store_true', help='enable auto-staking')

        # create a parser for 'delegate' command
        delegate_parser = subparsers.add_parser('delegate', help='Query and set delegations')
        delegate_parser.add_argument('--address', type=address_type, help='target address to perform operations')
        delegate_parser.add_argument('--set', action='store_true', help='set new delegations')

        # create a parser for 'prep' command
        prep_parser = subparsers.add_parser('prep', help='P-Rep management')
        prep_parser.add_argument('--register-test-preps', type=int, metavar='NUM',
                                 help='register NUM of P-Reps for testing')
        prep_parser.add_argument('--get', type=address_type, metavar='ADDRESS', help='get P-Rep information')
        prep_parser.add_argument('--get-preps', action='store_true', help='get all P-Reps information')

        args = parser.parse_args()
        getattr(self, args.command)(args)

    @staticmethod
    def gov(args):
        gov.run(args)

    @staticmethod
    def balance(args):
        icx.run('balance', args)

    @staticmethod
    def transfer(args):
        icx.run('transfer', args)

    @staticmethod
    def iscore(args):
        iscore.run(args)

    @staticmethod
    def stake(args):
        stake.run(args)

    @staticmethod
    def delegate(args):
        delegate.run(args)

    @staticmethod
    def prep(args):
        prep.run(args)


if __name__ == "__main__":
    try:
        Command()
    except KeyboardInterrupt:
        print('exit')
