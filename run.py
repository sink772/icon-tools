#!/usr/bin/env python

import argparse

from icx import icx
from iiss import iscore, stake, delegate
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
        subparsers.add_parser('gov', help='Check governance status')

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
        delegate_parser.add_argument('--prep', type=address_type, metavar='ADDRESS',
                                     help='get P-Rep register information')

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


if __name__ == "__main__":
    try:
        Command()
    except KeyboardInterrupt:
        print('exit')
