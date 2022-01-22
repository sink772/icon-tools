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
from util import get_icon_service, die, load_keystore
from util.txhandler import TxHandler


class OmmLendingPool(Score):
    LENDING_POOL = 'cxcb455f26a2c01c686fa7f30e1e3661642dd53c0d'

    def __init__(self, tx_handler: TxHandler):
        super().__init__(tx_handler, self.LENDING_POOL)

    def claim_rewards(self, wallet):
        return self.invoke(wallet, 'claimRewards')

    def ask_to_claim(self, keystore, passwd):
        confirm = input('\n==> Are you sure you want to claim? (y/n) ')
        if confirm == 'y':
            wallet = load_keystore(keystore, passwd)
            tx_hash = self.claim_rewards(wallet)
            self._tx_handler.ensure_tx_result(tx_hash, True)


def add_parser(cmd, subparsers):
    omm_parser = subparsers.add_parser('omm', help='[SCORE] OMM Finance')
    omm_parser.add_argument('--claim', action='store_true', help='claim rewards that has been received')

    # register method
    setattr(cmd, 'omm', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    lending_pool = OmmLendingPool(tx_handler)
    if args.claim:
        if not args.keystore:
            die('Error: keystore should be specified to claim')
        lending_pool.ask_to_claim(args.keystore, args.password)