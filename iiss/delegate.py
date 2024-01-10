# Copyright 2020 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse

from iconsdk.exception import JSONRPCException

from iiss.prep import PRep
from score.chain import ChainScore
from util import die, in_icx, print_response
from util.checks import address_type


class Delegate(object):

    def __init__(self, tx_handler):
        self._tx_handler = tx_handler
        self._chain = ChainScore(tx_handler)
        self._prep = PRep(tx_handler)

    def query(self, address):
        params = {
            "address": address
        }
        return self._chain.call("getDelegation", params)

    def set(self, wallet, delegations):
        delegation_list = []
        for address, value in delegations.items():
            if int(value, 16) > 0:
                delegation_list.append({"address": address, "value": value})
        params = {
            "delegations": delegation_list
        }
        return self._chain.invoke(wallet, "setDelegation", params)

    def get_total_delegated(self, address):
        result = self.query(address)
        return int(result['totalDelegated'], 16)

    def ask_to_set(self, result, keystore):
        confirm = input('\n==> Are you sure you want to set new delegations? (y/n) ')
        if confirm == 'y':
            delegations = self._get_new_delegations(result)
            wallet = keystore.get_wallet()
            tx_hash = self.set(wallet, delegations)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def _get_new_delegations(self, result):
        delegations = self.convert_to_map(result['delegations'])
        voting_power = int(result['votingPower'], 16)
        self.print_delegations(delegations, voting_power)
        while True:
            try:
                confirm = input('\n==> The address you want to set (or [s,l,q,?]): ')
                if len(confirm) == 1:
                    if confirm == 's':
                        return delegations
                    elif confirm == 'l':
                        self.print_delegations(delegations, voting_power)
                        continue
                    elif confirm == 'q':
                        die('exit')
                    elif confirm == '?':
                        print('s - set new delegations')
                        print('l - list current delegations')
                        print('q - quit')
                        print('? - show this help messages')
                        continue
                    else:
                        raise ValueError(f'Error: invalid input: {confirm}')
                address = address_type(confirm)
                self._prep.print_prep_info(address)
                maximum = voting_power + int(delegations.get(address, '0x0'), 16)
                amount = self._check_value(input(f'Delegation amount (max: {maximum}): '), maximum)
                if amount == 0:
                    del delegations[address]
                else:
                    delegations[address] = hex(amount)
                voting_power = maximum - amount
                self.print_delegations(delegations, voting_power)
            except KeyboardInterrupt:
                die('exit')
            except argparse.ArgumentTypeError:
                print('Error: invalid address')
                continue
            except ValueError as e:
                print(e.__str__())
                continue
            except JSONRPCException:
                continue

    @staticmethod
    def convert_to_map(delegation_list):
        delegations = {}
        for delegation in delegation_list:
            address = delegation["address"]
            value = delegation["value"]
            delegations[address] = value
        return delegations

    @staticmethod
    def _check_value(value: str, maximum: int):
        try:
            amount = int(value)
            if 0 <= amount <= maximum:
                return amount
            raise ValueError(f'Error: value should be 0 <= (value) <= {maximum}')
        except ValueError:
            raise ValueError(f'Error: value should be integer')

    @staticmethod
    def print_delegations(delegations, voting_power, header='delegations'):
        print()
        print_response(header, delegations)
        print('Remaining votingPower =', voting_power, f"({in_icx(voting_power)} ICX)")

    @staticmethod
    def print_status(address, result):
        print('\n[Delegation]')
        print_response(address, result)


def add_parser(cmd, subparsers):
    delegate_parser = subparsers.add_parser('delegate', help='Query and set delegations')
    delegate_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    delegate_parser.add_argument('--set', action='store_true', help='set new delegations')

    # register method
    setattr(cmd, 'delegate', run)


def run(args):
    delegate = Delegate(args.txhandler)
    address = args.address if args.address else args.keystore.address
    result = delegate.query(address)
    delegate.print_status(address, result)
    if args.set:
        delegate.ask_to_set(result, args.keystore)
