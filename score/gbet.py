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
from score.token import IRC2Token
from util import print_response, in_icx


class GBetSkill(Score):
    SKILL_ADDRESS = "cx2dc662031f3d62bcdba4f63e9bf827767c847565"

    def __init__(self, tx_handler):
        super().__init__(tx_handler, self.SKILL_ADDRESS)

    def get_allocated_claim_amt(self, nft_id):
        return self.call("getAllocatedClaimAmt", {"nftId": nft_id})

    def claim_allocated_amt(self, wallet, nft_id):
        return self.invoke(wallet, 'claimAllocatedAmt', {"nftId": nft_id})

    def print_claim_amount(self, nft_id):
        result = self.get_allocated_claim_amt(nft_id)
        print_response(f'#{nft_id}', result)
        total = int(result["total"], 16)
        print(f'Total amount: {in_icx(total)} GBET')
        return total

    def ask_to_claim(self, keystore, nft_id):
        confirm = input('\n==> Are you sure you want to claim? (y/n) ')
        if confirm == 'y':
            wallet = keystore.get_wallet()
            tx_hash = self.claim_allocated_amt(wallet, nft_id)
            self._tx_handler.ensure_tx_result(tx_hash, True)


def add_parser(cmd, subparsers):
    gbet_parser = subparsers.add_parser('gbet', help='[SCORE] GangstaBet')
    gbet_parser.add_argument('--claim', type=int, metavar='NFT_ID', help='claim the allocated GBET amount')

    # register method
    setattr(cmd, 'gbet', run)


def run(args):
    if args.claim and args.claim > 0:
        gbet = GBetSkill(args.txhandler)
        nft_id = args.claim
        amount = gbet.print_claim_amount(nft_id)
        if amount > 0:
            gbet.ask_to_claim(args.keystore, nft_id)
    else:
        token = IRC2Token(args.txhandler, 'gbet')
        address = args.keystore.address
        token.print_balance(address)
