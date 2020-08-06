#!/usr/bin/env python

import argparse
import sys

from gov import check


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Available commands', metavar='command')
    subparsers.required = True
    subparsers.dest = 'command'

    # create a parser for 'gov' command
    gov_parser = subparsers.add_parser('gov', help='Check governance status')
    gov_parser.add_argument('endpoint', type=str, nargs='?', default="mainnet", help='an endpoint for connection')

    args = parser.parse_args()
    print(args)
    if args.command == 'gov':
        check.run(args.endpoint)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("exit")
