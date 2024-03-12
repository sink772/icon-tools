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
from util import print_response
from util.checks import address_type


class IScore(object):

    def __init__(self, tx_handler):
        self._tx_handler = tx_handler
        self._chain = ChainScore(tx_handler)

    def query(self, address, height=None):
        params = {
            "address": address
        }
        return self._chain.call("queryIScore", params, height)

    def claim(self, wallet):
        return self._chain.invoke(wallet, "claimIScore")

    def ask_to_claim(self, keystore):
        confirm = input('\n==> Are you sure you want to claim the IScore? (y/n) ')
        if confirm == 'y':
            wallet = keystore.get_wallet()
            tx_hash = self.claim(wallet)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def print_status(self, address, result=None, height=None):
        print('\n[IScore]')
        if result is None:
            result = self.query(address, height)
        print_response(address, result)


def add_parser(cmd, subparsers):
    iscore_parser = subparsers.add_parser('iscore', help='Query and claim IScore')
    iscore_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    iscore_parser.add_argument('--claim', action='store_true', help='claim the reward that has been received')
    iscore_parser.add_argument('--height', type=int, help='target block height')

    # register method
    setattr(cmd, 'iscore', run)


def run(args):
    iscore = IScore(args.txhandler)
    address = args.address if args.address else args.keystore.address
    iscore.print_status(address, result=None, height=args.height)
    if args.claim:
        iscore.ask_to_claim(args.keystore)
