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

from iiss.delegate import Delegate
from score.chain import ChainScore
from util import die, in_icx, in_loop, print_response, get_icon_service, get_address_from_keystore, load_keystore


class Stake(object):

    def __init__(self, service):
        self._chain = ChainScore(service)
        self._icon_service = service

    def balance(self, address):
        return self._icon_service.get_balance(address)

    def query(self, address):
        params = {
            "address": address
        }
        return self._chain.call("getStake", params)

    def set(self, wallet, amount):
        params = {
            "value": in_loop(amount)
        }
        return self._chain.invoke(wallet, "setStake", params)

    def ask_to_set(self, address, current_stake, keystore):
        confirm = input('\n==> Are you sure you want to set new staking amount? (y/n) ')
        if confirm == 'y':
            balance = self.balance(address)
            status = {
                'staked': in_icx(current_stake),
                'unstaked': in_icx(balance),
            }
            total_icx = in_icx(current_stake + balance)
            print_response('Balance (in ICX)', status)
            print('Total ICX balance =', total_icx)
            input_value = input('\n==> New staking amount (in ICX)? ')
            new_amount = self._check_value(input_value, int(total_icx))
            self._check_total_delegated(address, in_loop(new_amount))
            print('Requested amount =', new_amount, f'({in_loop(new_amount)} loop)')
            wallet = load_keystore(keystore)
            tx_hash = self.set(wallet, new_amount)
            print(f'\n==> Success: https://tracker.icon.foundation/transaction/{tx_hash}')

    @staticmethod
    def print_status(address, result):
        print('[Stake]')
        print_response(address, result)
        print('StakedICX =', int(result['stake'], 16) / 10**18)

    @staticmethod
    def _check_value(value: str, maximum: int):
        try:
            amount = int(value)
            if 0 <= amount <= maximum:
                return amount
            die(f'Error: value should be 0 <= (value) <= {maximum}')
        except ValueError:
            die(f'Error: value should be integer')

    def _check_total_delegated(self, address, amount):
        total_delegated = Delegate(self._icon_service).get_total_delegated(address)
        if amount <= total_delegated:
            die(f'Error: amount ({amount}) should be larger than the current total delegated ({total_delegated})')


def run(args):
    icon_service = get_icon_service(args.endpoint)
    stake = Stake(icon_service)
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    elif args.address:
        address = args.address
    else:
        die('Error: keystore or address should be specified')
    result = stake.query(address)
    current_stake = int(result['stake'], 16)
    stake.print_status(address, result)
    if args.set:
        if not args.keystore:
            die('Error: keystore should be specified to set staking')
        stake.ask_to_set(address, current_stake, args.keystore)
