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

from iiss.stake import Stake
from util import die, in_icx, get_icon_service, get_address_from_keystore, print_response, load_keystore, TxHandler


class ICX(object):

    def __init__(self, service):
        self._icon_service = service

    def balance(self, address, is_all):
        _balance = self._icon_service.get_balance(address)
        status = {
            'ICX (avail)': in_icx(_balance)
        }
        if is_all:
            result = Stake(self._icon_service).query(address)
            current_stake = int(result['stake'], 16)
            status['ICX (stake)'] = in_icx(current_stake)
            status['Total ICX  '] = in_icx(_balance + current_stake)
        print('\n[Balance]')
        print_response(address, status)
        return _balance

    def transfer(self, address, args):
        _balance = self.balance(address, False)
        if args.amount:
            _amount = args.amount
        else:
            value = input('\n==> Amount of transfer (in loop)? ')
            try:
                _amount = int(value)
            except ValueError:
                die(f'Error: value should be integer')
        self.ensure_amount(_amount, _balance)
        if self.ask_to_confirm(args.to, _balance, _amount):
            wallet = load_keystore(args.keystore, args.password)
            _tx_handler = TxHandler(self._icon_service)
            tx_hash = _tx_handler.transfer(wallet, args.to, _amount)
            print(f'\n==> Success: https://tracker.icon.foundation/transaction/{tx_hash}')

    @staticmethod
    def ensure_amount(amount, maximum):
        if 0 < amount < maximum:
            return amount
        die(f'Error: value should be 0 < (value) < {maximum}')

    @staticmethod
    def ask_to_confirm(address, current_balance, amount):
        details = {
            "recipient": address,
            "amount": f"{amount} ({in_icx(amount)} ICX)",
            "estimated balance after transfer": f"{in_icx(current_balance - amount)} ICX"
        }
        print()
        print_response('Details', details)
        confirm = input('\n==> Are you sure you want to transfer the ICX? (y/n) ')
        if confirm == 'y':
            return True
        return False


def run(action, args):
    icon_service = get_icon_service(args.endpoint)
    icx = ICX(icon_service)
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    elif action == 'balance' and args.address:
        address = args.address
    else:
        die('Error: keystore or address should be specified')
    if action == 'balance':
        icx.balance(address, args.all)
    elif action == 'transfer':
        icx.transfer(address, args)
    else:
        die('Error: unknown action')
