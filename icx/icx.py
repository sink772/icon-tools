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
from util import die, in_icx, in_loop, print_response
from util.checks import address_type


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
        print('\n[ICX Balance]')
        print_response(address, status)
        return balance

    def transfer(self, address, to, amount, keystore):
        balance = self.balance(address, False)
        default_step = 100_000
        step_price = self.get_step_price()
        tx_fee = default_step * step_price
        maximum = balance - tx_fee
        if not amount:
            value = input('\n==> Amount of transfer in loop (or [a]ll): ')
            try:
                if len(value) == 1 and value == 'a':
                    amount = maximum
                elif value.endswith("icx"):
                    amount = in_loop(int(value[:-3]))
                else:
                    amount = int(value)
            except ValueError:
                die(f'Error: value should be integer')
        self.ensure_amount(amount, maximum)
        if self.ask_to_confirm(to, balance, amount, tx_fee):
            wallet = keystore.get_wallet()
            tx_hash = self._tx_handler.transfer(wallet, to, amount,
                                                default_step if to.startswith('hx') else None)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def get_step_price(self):
        try:
            gov = Governance(self._tx_handler)
            step_price = int(gov.get_step_price(), 16)
        except JSONRPCException:
            step_price = 12_500_000_000
        return step_price

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


def add_parser(cmd, subparsers):
    # create a parser for 'icx' command
    icx_parser = subparsers.add_parser('icx', help='ICX operations')
    icx_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    icx_parser.add_argument('--all', action='store_true', help='include the staked ICX')
    icx_parser.add_argument('--transfer', type=address_type, metavar='TO', help='transfer to the given address')
    icx_parser.add_argument('--amount', type=int, help='the amount of ICX (in loop)')
    icx_parser.add_argument('--private', action='store_true', help='show the private key')

    # register methods
    setattr(cmd, 'icx', run)


def run(args):
    icx = ICX(args.txhandler)
    address = args.address if args.address else args.keystore.address
    if args.transfer:
        to = args.transfer
        icx.transfer(address, to, args.amount, args.keystore)
    elif args.private:
        wallet = args.keystore.get_wallet()
        print("private key =", wallet.get_private_key())
    else:
        icx.balance(address, args.all)
