#!/usr/bin/env python

import argparse

from icx import icx
from iiss import iscore, stake, delegate, prep, info
from score import gov, audit


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

        # add subcommand parsers
        modules = [gov, audit, icx, iscore, stake, delegate, info, prep]
        for mod in modules:
            mod.add_parser(self, subparsers)

        args = parser.parse_args()
        getattr(self, args.command)(args)


if __name__ == "__main__":
    try:
        Command()
    except KeyboardInterrupt:
        print('exit')
