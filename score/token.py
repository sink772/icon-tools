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

from score import Score
from score.baln import BalancedDex
from util import get_address_from_keystore, die, print_response, load_keystore, in_icx, get_icon_service
from util.checks import address_type
from util.txhandler import TxHandler


class IRC2Token(Score):
    TOKEN_MAP = {
        'sicx': 'cx2609b924e33ef00b648a409245c7ea394c467824',
        'baln': 'cxf61cd5a45dc9f91c15aa65831a30a90d59a09619',
        'bnusd': 'cx88fd7df7ddff82f7cc735c871dc519838cb235bb',
        'omm': 'cx1a29259a59f463a67bb2ef84398b30ca56b5830a',
        'cft': 'cx2e6d0fc0eca04965d06038c8406093337f085fcf',
        'gbet': 'cx6139a27c15f1653471ffba0b4b88dc15de7e3267'
    }

    def __init__(self, tx_handler: TxHandler, name: str):
        self._name = name
        address = self.TOKEN_MAP.get(name)
        if not address:
            die(f'Error: supported tokens: {list(self.TOKEN_MAP.keys())}')
        super().__init__(tx_handler, address)

    def balance(self, address):
        return self.call("balanceOf", {"_owner": address})

    def transfer(self, wallet, to, value, data=None):
        param = {
            "_to": to,
            "_value": value
        }
        if data is not None:
            param["_data"] = data
        return self.invoke(wallet, 'transfer', param)

    def print_balance(self, address):
        bal = self.balance(address)
        price_in_loop = int(bal, 16)
        price_in_icx = in_icx(price_in_loop)
        print(f'\n[Token Balance]')
        print(f'"{bal}" ({price_in_icx:.2f} {self._name.upper()})')
        return price_in_loop

    def ask_to_transfer(self, args, to, to_token=None):
        if not args.keystore:
            die('Error: keystore should be specified')
        address = get_address_from_keystore(args.keystore)
        maximum = self.print_balance(address)
        amount = maximum
        value = input('\n==> Amount of transfer in loop (or [a]ll): ')
        try:
            if len(value) == 1 and value == 'a':
                pass
            else:
                amount = int(value)
        except ValueError:
            die(f'Error: value should be integer')
        self.ensure_amount(amount, maximum)
        if self.ask_to_confirm(to, maximum, amount):
            wallet = load_keystore(args.keystore, args.password)
            data = None
            if to_token is not None and address_type(to_token) == to_token:
                data = b'{"method":"_swap","params":{"toToken":"' + to_token.encode('utf-8') + b'"}}'
            tx_hash = self.transfer(wallet, to, amount, data)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def swap(self, args, to_token):
        self.ask_to_transfer(args, BalancedDex.DEX_ADDRESS, to_token)

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
            "estimated balance after transfer": f"{in_icx(balance - amount)}"
        }
        print()
        print_response('Details', details)
        confirm = input('\n==> Are you sure you want to transfer? (y/n) ')
        if confirm == 'y':
            return True
        return False


def add_parser(cmd, subparsers):
    token_parser = subparsers.add_parser('token', help='Token (IRC2) manipulation')
    token_parser.add_argument('--name', type=str, required=True, help='token name')
    token_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    token_parser.add_argument('--transfer', type=address_type, metavar='TO', help='transfer token to the given address')

    # register method
    setattr(cmd, 'token', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    token = IRC2Token(tx_handler, args.name)
    address = args.address
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    if not address:
        die('Error: keystore or address should be specified')
    if args.transfer:
        to = args.transfer
        token.ask_to_transfer(args, to)
    else:
        token.print_balance(address)
