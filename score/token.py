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
from util import die, print_response, in_icx, in_loop
from util.checks import address_type


class IRC2Token(Score):
    TOKEN_MAP = {
        'sicx': 'cx2609b924e33ef00b648a409245c7ea394c467824',
        'baln': 'cxf61cd5a45dc9f91c15aa65831a30a90d59a09619',
        'bnusd': 'cx88fd7df7ddff82f7cc735c871dc519838cb235bb',
        'iusdc': 'cxae3034235540b924dfcc1b45836c293dcc82bfb7',
        'usds': 'cxbb2871f468a3008f80b08fdde5b8b951583acf06',
        'omm': 'cx1a29259a59f463a67bb2ef84398b30ca56b5830a',
        'cft': 'cx2e6d0fc0eca04965d06038c8406093337f085fcf',
        'gbet': 'cx6139a27c15f1653471ffba0b4b88dc15de7e3267'
    }

    def __init__(self, tx_handler, name: str):
        self._name = name
        address = self.TOKEN_MAP.get(name)
        if not address:
            die(f'Error: supported tokens: {list(self.TOKEN_MAP.keys())}')
        super().__init__(tx_handler, address)

    @property
    def name(self):
        return self._name

    def balance(self, address):
        hex_value = self.call("balanceOf", {"_owner": address})
        return hex_value, int(hex_value, 16)

    def transfer(self, wallet, to, value, data=None):
        param = {
            "_to": to,
            "_value": value
        }
        if data is not None:
            param["_data"] = data
        return self.invoke(wallet, 'transfer', param)

    def print_balance(self, address):
        hex_value, price_in_loop = self.balance(address)
        price_in_icx = in_icx(price_in_loop)
        print(f'\n[Token Balance]')
        print(f'"{hex_value}" ({price_in_icx:.2f} {self._name.upper()})')
        return price_in_loop

    def ask_to_transfer(self, keystore, to, to_token=None):
        address = keystore.address
        maximum = self.print_balance(address)
        amount = maximum
        value = input('\n==> Amount of transfer in loop (or [a]ll): ')
        try:
            if len(value) == 1 and value == 'a':
                pass
            elif value.endswith("icx"):
                amount = in_loop(int(value[:-3]))
            else:
                amount = int(value)
        except ValueError:
            die(f'Error: value should be integer')
        self.ensure_amount(amount, maximum)
        if self.ask_to_confirm(to, maximum, amount):
            wallet = keystore.get_wallet()
            data = None
            if to_token is not None and address_type(to_token) == to_token:
                data = b'{"method":"_swap","params":{"toToken":"' + to_token.encode('utf-8') + b'"}}'
            tx_hash = self.transfer(wallet, to, amount, data)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def swap(self, keystore, to_token):
        self.ask_to_transfer(keystore, BalancedDex.DEX_ADDRESS, to_token)

    @staticmethod
    def ensure_amount(amount, maximum):
        if 0 < amount <= maximum:
            return amount
        die(f'Error: value should be 0 < (value) <= {maximum}')

    def ask_to_confirm(self, address, balance, amount):
        details = {
            "recipient": address,
            "amount": f"{amount} ({in_icx(amount)} {self._name.upper()})",
            "estimated balance after transfer": f"{in_icx(balance - amount)}"
        }
        print()
        print_response('Details', details)
        confirm = input('\n==> Are you sure you want to transfer? (y/n) ')
        if confirm == 'y':
            return True
        return False


def add_parser(cmd, subparsers):
    token_parser = subparsers.add_parser('token', help='Token (IRC2) operations')
    token_parser.add_argument('--name', type=str, required=True, help='token name')
    token_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    token_parser.add_argument('--transfer', type=address_type, metavar='TO', help='transfer token to the given address')
    token_parser.add_argument('--swap', type=str, metavar='TOKEN_NAME', help='swap to target token')

    # register method
    setattr(cmd, 'token', run)


def run(args):
    token = IRC2Token(args.txhandler, args.name)
    address = args.address if args.address else args.keystore.address
    if args.transfer:
        to = args.transfer
        token.ask_to_transfer(args.keystore, to)
    elif args.swap:
        token2 = args.swap
        pool_id = BalancedDex(args.txhandler).print_pool_id(token.name, token2)
        if pool_id == 0:
            die('Error: not supported pool')
        target = IRC2Token(args.txhandler, token2)
        target.print_balance(address)
        token.swap(args.keystore, target.address)
    else:
        token.print_balance(address)
