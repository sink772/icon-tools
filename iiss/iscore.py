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

from score.chain import ChainScore
from util import die, in_icx, print_response, get_icon_service, get_address_from_keystore, load_keystore
from util.checks import address_type
from util.txhandler import TxHandler


class IScore(object):

    def __init__(self, tx_handler):
        self._tx_handler = tx_handler
        self._chain = ChainScore(tx_handler)

    def query(self, address):
        params = {
            "address": address
        }
        return self._chain.call("queryIScore", params)

    def claim(self, wallet):
        return self._chain.invoke(wallet, "claimIScore")

    def ask_to_claim(self, keystore, passwd):
        confirm = input('\n==> Are you sure you want to claim the IScore? (y/n) ')
        if confirm == 'y':
            wallet = load_keystore(keystore, passwd)
            tx_hash = self.claim(wallet)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def print_status(self, address, result=None):
        print('\n[IScore]')
        if result is None:
            result = self.query(address)
        print_response(address, result)
        print('EstimatedICX =', in_icx(int(result['estimatedICX'], 16)))


def add_parser(cmd, subparsers):
    iscore_parser = subparsers.add_parser('iscore', help='Query and claim IScore')
    iscore_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    iscore_parser.add_argument('--claim', action='store_true', help='claim the reward that has been received')

    # register method
    setattr(cmd, 'iscore', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    iscore = IScore(tx_handler)
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    elif args.address:
        address = args.address
    else:
        die('Error: keystore or address should be specified')
    iscore.print_status(address)
    if args.claim:
        if not args.keystore:
            die('Error: keystore should be specified to claim')
        iscore.ask_to_claim(args.keystore, args.password)
