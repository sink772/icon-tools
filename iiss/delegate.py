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
import getpass

from iconsdk.exception import KeyStoreException
from iconsdk.wallet.wallet import KeyWallet

from run import address_type
from score.chain import ChainScore
from util import die, print_response, get_icon_service, get_address_from_keystore


class Delegate(object):

    def __init__(self, service):
        self._chain = ChainScore(service)
        self._icon_service = service

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
            try:
                passwd = getpass.getpass()
                wallet = KeyWallet.load(keystore.name, passwd)
                tx_hash = self.set(wallet, delegations)
                print(f'\n==> Success: https://tracker.icon.foundation/transaction/{tx_hash}')
            except KeyStoreException as e:
                die(e.message)

    def _get_new_delegations(self, result):
        delegations = self._convert_to_map(result['delegations'])
        voting_power = int(result['votingPower'], 16)
        self._print_delegations(delegations, voting_power)
        while True:
            try:
                confirm = input('\n==> The address you want to set (\'q\' for finish): ')
                if confirm == 'q':
                    return delegations
                address = address_type(confirm)
                maximum = voting_power + int(delegations.get(address, '0x0'), 16)
                amount = self._check_value(input(f'Delegation amount (max: {maximum}): '), maximum)
                delegations[address] = hex(amount)
                voting_power = maximum - amount
                self._print_delegations(delegations, voting_power)
            except KeyboardInterrupt:
                die('exit')
            except argparse.ArgumentTypeError:
                print('Error: invalid address')
                continue
            except ValueError as e:
                print(e.__str__())
                continue

    @staticmethod
    def _convert_to_map(delegation_list):
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
    def _print_delegations(delegations, voting_power):
        print()
        print_response('delegations', delegations)
        print('Remaining votingPower =', voting_power)

    @staticmethod
    def print_status(address, result):
        print('[Delegation]')
        print_response(address, result)


def run(args):
    icon_service = get_icon_service(args.endpoint)
    delegate = Delegate(icon_service)
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    elif args.address:
        address = args.address
    else:
        die('Error: keystore or address should be specified')
    result = delegate.query(address)
    delegate.print_status(address, result)
    if args.set:
        if not args.keystore:
            die('Error: keystore should be specified to set delegations')
        delegate.ask_to_set(result, args.keystore)
