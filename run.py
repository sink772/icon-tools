#!/usr/bin/env python

import argparse

from iiss import iscore, stake
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

        subparsers = parser.add_subparsers(title='Available commands', metavar='command')
        subparsers.required = True
        subparsers.dest = 'command'

        # create a parser for 'gov' command
        subparsers.add_parser('gov', help='Check governance status')

        # create a parser for 'iscore' command
        iscore_parser = subparsers.add_parser('iscore', help='Query and claim IScore')
        iscore_parser.add_argument('--address', type=address_type, help='target address to perform operations')
        iscore_parser.add_argument('--claim', action='store_true', help='claim the reward that has been received')

        # create a parser for 'stake' command
        stake_parser = subparsers.add_parser('stake', help='Query and set staking')
        stake_parser.add_argument('--address', type=address_type, help='target address to perform operations')
        stake_parser.add_argument('--set', action='store_true', help='set new staking amount')

        args = parser.parse_args()
        getattr(self, args.command)(args)

    @staticmethod
    def gov(args):
        gov.run(args.endpoint)

    @staticmethod
    def iscore(args):
        iscore.run(args)

    @staticmethod
    def stake(args):
        stake.run(args)


if __name__ == "__main__":
    try:
        Command()
    except KeyboardInterrupt:
        print('exit')
