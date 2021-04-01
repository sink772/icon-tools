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

from iconsdk.exception import JSONRPCException

from iiss.stake import Stake
from score.gov import Governance
from util import die, in_icx, get_icon_service, get_address_from_keystore, print_response, load_keystore
from util.txhandler import TxHandler


class ICX(object):

    def __init__(self, tx_handler):
        self._tx_handler = tx_handler

    def balance(self, address, is_all):
        balance = self._tx_handler.get_balance(address)
        status = {
            'ICX (avail)': in_icx(balance)
        }
        if is_all:
            result = Stake(self._tx_handler).query(address)
            current_stake = int(result['stake'], 16)
            status['ICX (stake)'] = in_icx(current_stake)
            status['Total ICX  '] = in_icx(balance + current_stake)
        print('\n[Balance]')
        print_response(address, status)
        return balance

    def transfer(self, address, args):
        balance = self.balance(address, False)
        tx_fee = self.get_default_tx_fee()
        maximum = balance - tx_fee
        if args.amount:
            amount = args.amount
        else:
            value = input('\n==> Amount of transfer in loop (or [a]ll): ')
            try:
                if len(value) == 1 and value == 'a':
                    amount = maximum
                else:
                    amount = int(value)
            except ValueError:
                die(f'Error: value should be integer')
        self.ensure_amount(amount, maximum)
        if self.ask_to_confirm(args.to, balance, amount, tx_fee):
            wallet = load_keystore(args.keystore, args.password)
            tx_hash = self._tx_handler.transfer(wallet, args.to, amount)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def get_default_tx_fee(self):
        try:
            gov = Governance(self._tx_handler, None)
            step_price = int(gov.get_step_price(), 16)
        except JSONRPCException:
            step_price = 12_500_000_000
        default_step = 100_000
        return step_price * default_step

    @staticmethod
    def ensure_amount(amount, maximum):
        if 0 < amount <= maximum:
            return amount
        die(f'Error: value should be 0 < (value) <= {maximum}')

    @staticmethod
    def ask_to_confirm(address, balance, amount, tx_fee):
        details = {
            "recipient": address,
            "amount": f"{amount} ({in_icx(amount)} ICX)",
            "estimated balance after transfer": f"{in_icx(balance - amount - tx_fee)} ICX"
        }
        print()
        print_response('Details', details)
        confirm = input('\n==> Are you sure you want to transfer the ICX? (y/n) ')
        if confirm == 'y':
            return True
        return False


def run(action, args):
    icon_service, nid = get_icon_service(args.endpoint)
    tx_handler = TxHandler(icon_service, nid)
    icx = ICX(tx_handler)
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
