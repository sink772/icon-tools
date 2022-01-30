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

import json

from score import Score
from util import get_icon_service, get_address_from_keystore, die, print_response, in_icx, load_keystore
from util.checks import address_type
from util.txhandler import TxHandler


class BalancedDex(Score):
    DEX_ADDRESS = "cxa0af3165c08318e988cb30993b3048335b94af6c"

    def __init__(self, tx_handler: TxHandler):
        super().__init__(tx_handler, self.DEX_ADDRESS)

    def balance(self, pool_id, address):
        return self.call("balanceOf", {"_owner": address, "_id": pool_id})

    def get_price(self, pool_id):
        return self.call("getPrice", {"_id": pool_id})

    def get_pool_stats(self, pool_id):
        return self.call("getPoolStats", {"_id": pool_id})

    def get_pool_id(self, token1, token2):
        return self.call("getPoolId", {'_token1Address': token1, '_token2Address': token2})

    def transfer(self, wallet, to, pool_id, value):
        return self.invoke(wallet, 'transfer', {
            '_to': to,
            '_id': pool_id,
            '_value': value,
            '_data': '0x' + bytes.hex(json.dumps({"method": "stake"}).encode())
        })

    def print_balance(self, pool_id, address):
        bal = self.balance(pool_id, address)
        price_in_loop = int(bal, 16)
        price_in_icx = in_icx(price_in_loop)
        print('\n[Balance]')
        print(f'"{bal}" ({price_in_loop}, {price_in_icx}) ')
        return price_in_loop

    def print_pool_stats(self, pool_id):
        stats = self.get_pool_stats(pool_id)
        pool_name = stats['name']
        price = int(stats['price'], 16)
        base = int(stats['base'], 16)
        quote = int(stats['quote'], 16)
        base_name, quote_name = pool_name.split('/')

        print()
        print_response(pool_name, {
            'price': f'{price} ({in_icx(price):.4f})',
            'base': f'{base} ({in_icx(base):.2f} {base_name})',
            'quote': f'{quote} ({in_icx(quote):.2f} {quote_name})'
        })

    def print_pool_id(self, token1, token2):
        from score.token import IRC2Token
        addr1 = IRC2Token(self._tx_handler, token1.lower()).address
        addr2 = IRC2Token(self._tx_handler, token2.lower()).address
        pool_id = int(self.get_pool_id(addr1, addr2), 16)
        print(f'{token1}/{token2} = {pool_id}')
        return pool_id

    def transfer_token(self, pool_id, args):
        if not args.keystore:
            die('Error: keystore should be specified')
        address = get_address_from_keystore(args.keystore)
        maximum = self.print_balance(pool_id, address)
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
        if self.ask_to_confirm(args.to, maximum, amount):
            wallet = load_keystore(args.keystore, args.password)
            tx_hash = self.transfer(wallet, args.to, pool_id, amount)
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
            "estimated balance after transfer": f"{in_icx(balance - amount)}"
        }
        print()
        print_response('Details', details)
        confirm = input('\n==> Are you sure you want to transfer? (y/n) ')
        if confirm == 'y':
            return True
        return False


def add_parser(cmd, subparsers):
    baln_parser = subparsers.add_parser('baln', help='[SCORE] Balanced')
    baln_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    baln_parser.add_argument('--balance', type=int, metavar='POOL_ID', help='get balance of the given pool id')
    baln_parser.add_argument('--pool_stats', type=int, metavar='POOL_ID', help='get pool stats of the given pool id')
    baln_parser.add_argument('--pool_id', type=str, metavar='TOKEN_PAIR', help='get pool id of the given token pair')
    baln_parser.add_argument('--transfer', type=int, metavar='POOL_ID', help='transfer LP tokens to another address')
    baln_parser.add_argument('--to', type=address_type, help='the recipient address')

    # register method
    setattr(cmd, 'baln', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    dex = BalancedDex(tx_handler)
    if args.balance:
        pool_id = args.balance
        address = args.address
        if args.keystore:
            address = get_address_from_keystore(args.keystore)
        if not address:
            die('Error: keystore or address should be specified')
        dex.print_balance(pool_id, address)
    elif args.pool_stats:
        pool_id = args.pool_stats
        dex.print_pool_stats(pool_id)
    elif args.pool_id:
        token_pair = args.pool_id
        token1, token2 = token_pair.split('/')
        dex.print_pool_id(token1, token2)
    elif args.transfer:
        pool_id = args.transfer
        if not args.to:
            die('Error: recipient address should be specified')
        dex.transfer_token(pool_id, args)
