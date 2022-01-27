# Copyright 2022 ICON Foundation
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

from icx.icx import ICX
from score import Score
from score.token import IRC2Token
from util import get_icon_service, die, load_keystore, get_address_from_keystore, in_icx, print_response
from util.txhandler import TxHandler


class StakedICXManager(Score):
    STAKING_MAN = 'cx43e2eec79eb76293c298f2b17aec06097be606e0'

    def __init__(self, tx_handler: TxHandler):
        super().__init__(tx_handler, self.STAKING_MAN)

    def stake_icx(self, wallet, to, value):
        return self.invoke(wallet, 'stakeICX', {'_to': to}, value=value)

    def ask_to_stake(self, address, keystore, password):
        maximum = ICX(self._tx_handler).balance(address, False)
        amount = maximum
        value = input('\n==> Amount of transfer in loop: ')
        try:
            amount = int(value)
        except ValueError:
            die(f'Error: value should be integer')
        self.ensure_amount(amount, maximum)
        if self.ask_to_confirm(self.STAKING_MAN, maximum, amount):
            wallet = load_keystore(keystore, password)
            tx_hash = self.stake_icx(wallet, wallet.get_address(), amount)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    @staticmethod
    def ensure_amount(amount, maximum):
        if 0 < amount <= maximum:
            return amount
        die(f'Error: value should be 0 < (value) <= {maximum}')

    @staticmethod
    def ask_to_confirm(address, balance, amount):
        details = {
            "recipient": address,
            "amount": f"{amount} ({in_icx(amount)})",
            "estimated balance after stake": f"{in_icx(balance - amount)} ICX"
        }
        print()
        print_response('Details', details)
        confirm = input('\n==> Are you sure you want to stake? (y/n) ')
        if confirm == 'y':
            return True
        return False


def add_parser(cmd, subparsers):
    sicx_parser = subparsers.add_parser('sicx', help='[SCORE] Staked ICX')
    sicx_parser.add_argument('--stake', action='store_true', help='stake the given ICX')

    # register method
    setattr(cmd, 'sicx', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    if not args.keystore:
        die('Error: keystore should be specified to run')
    address = get_address_from_keystore(args.keystore)
    token = IRC2Token(tx_handler, 'sicx')
    token.print_balance(address)
    if args.stake:
        StakedICXManager(tx_handler).ask_to_stake(address, args.keystore, args.password)
