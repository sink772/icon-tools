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
from util import convert


class OmmFeeDistribution(Score):
    DISTRIBUTION = 'cx553b05df18e9d7c00d8bf4675e579cbbb23c4b30'

    def __init__(self, tx_handler):
        super().__init__(tx_handler, self.DISTRIBUTION)

    def claimable_fee(self, address):
        return self.call('getClaimableFee', {'user': address})

    def claim_rewards(self, wallet):
        return self.invoke(wallet, 'claimRewards')

    def print_claimable_fee(self, address):
        print('\n[ClaimableFee]')
        print(convert(self.claimable_fee(address)))

    def ask_to_claim(self, keystore):
        confirm = input('\n==> Are you sure you want to claim? (y/n) ')
        if confirm == 'y':
            wallet = keystore.get_wallet()
            tx_hash = self.claim_rewards(wallet)
            self._tx_handler.ensure_tx_result(tx_hash, True)


def add_parser(cmd, subparsers):
    omm_parser = subparsers.add_parser('omm', help='[SCORE] OMM Finance')
    omm_parser.add_argument('--claim', action='store_true', help='claim rewards that has been accrued')

    # register method
    setattr(cmd, 'omm', run)


def run(args):
    distribution = OmmFeeDistribution(args.txhandler)
    distribution.print_claimable_fee(args.keystore.address)
    if args.claim:
        distribution.ask_to_claim(args.keystore)
