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
from util import get_icon_service, get_address_from_keystore, die, print_response, load_keystore
from util.checks import address_type
from util.txhandler import TxHandler


class CraftReward(Score):
    REWARD_ADDRESS = "cx7ecb16e4c143b95e01d05933c17cb986cfe618e6"

    def __init__(self, tx_handler: TxHandler):
        super().__init__(tx_handler, self.REWARD_ADDRESS)

    def query_rewards(self, address):
        return self.call("queryRewards", {"_address": address})

    def query_lp_rewards(self, address):
        return self.call("queryLpRewards", {"_address": address})

    def claim_rewards(self, wallet):
        return self.invoke(wallet, 'claimRewards')

    def query_all_rewards(self, address):
        return {
            'liquidity': self.query_rewards(address),
            'lp_staking': self.query_lp_rewards(address)
        }

    def ask_to_claim(self, keystore, passwd):
        confirm = input('\n==> Are you sure you want to claim? (y/n) ')
        if confirm == 'y':
            wallet = load_keystore(keystore, passwd)
            tx_hash = self.claim_rewards(wallet)
            self._tx_handler.ensure_tx_result(tx_hash, True)


def add_parser(cmd, subparsers):
    cft_parser = subparsers.add_parser('cft', help='[SCORE] CraftNetwork')
    cft_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    cft_parser.add_argument('--claim', action='store_true', help='claim rewards that has been received')

    # register method
    setattr(cmd, 'cft', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    cft = CraftReward(tx_handler)
    address = args.address
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    if not address:
        die('Error: keystore or address should be specified')
    print_response(address, cft.query_all_rewards(address))
    if args.claim:
        if not args.keystore:
            die('Error: keystore should be specified to claim')
        cft.ask_to_claim(args.keystore, args.password)