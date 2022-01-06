# Copyright 2021 ICON Foundation
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

from iconsdk.exception import JSONRPCException
from iconsdk.wallet.wallet import KeyWallet

from score.chain import ChainScore
from util import die, in_loop, print_response, get_icon_service, load_keystore
from util.checks import address_type
from util.txhandler import TxHandler


class PRep(object):

    def __init__(self, tx_handler):
        self._tx_handler: TxHandler = tx_handler
        self._chain = ChainScore(tx_handler)

    def get_prep(self, address):
        params = {
            "address": address
        }
        return self._chain.call("getPRep", params)

    def get_preps(self):
        return self._chain.call("getPReps")

    def register_prep(self, wallet, params):
        return self._chain.invoke(wallet, "registerPRep", params, value=in_loop(2000))

    def set_stake(self, wallet, amount):
        params = {
            "value": amount
        }
        return self._chain.invoke(wallet, "setStake", params)

    def set_delegation(self, wallet, amount):
        params = {
            "delegations": [
                {
                    "address": wallet.get_address(),
                    "value": amount
                }
            ]
        }
        return self._chain.invoke(wallet, "setDelegation", params)

    def print_prep_info(self, prep_addr):
        print_response('P-Rep Info', self.get_prep(prep_addr))

    def print_preps_info(self):
        print_response('P-Reps Info', self.get_preps())

    @staticmethod
    def is_test_endpoint(endpoint):
        return endpoint in ('local', 'gochain')

    def register_test_preps(self, keystore, preps_num):
        god_wallet = load_keystore(keystore)
        delegate_value = self._tx_handler.get_balance(god_wallet.get_address()) // 100_000
        transfer_value = delegate_value + in_loop(3000)
        test_preps = []
        tx_hash = None
        for i in range(preps_num):
            wallet = KeyWallet.create()
            test_preps.append(wallet)
            tx_hash = self._tx_handler.transfer(god_wallet, wallet.get_address(), transfer_value)
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"registerPRep")
        for prep in test_preps:
            name = f"node_{prep.get_address()}"
            params = {
                "name": name,
                "country": "KOR",
                "city": "Seoul",
                "email": f"{name}@example.com",
                "website": f"https://{name}.example.com",
                "details": f"https://{name}.example.com/details",
                "p2pEndpoint": f"{name}.example.com:7100",
            }
            tx_hash = self.register_prep(prep, params)
            print(f"  [{prep.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"setStake")
        for prep in test_preps:
            tx_hash = self.set_stake(prep, delegate_value)
            print(f"  [{prep.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"setDelegation")
        for prep in test_preps:
            tx_hash = self.set_delegation(prep, delegate_value)
            print(f"  [{prep.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)


def add_parser(cmd, subparsers):
    prep_parser = subparsers.add_parser('prep', help='P-Rep management')
    prep_parser.add_argument('--register-test-preps', type=int, metavar='NUM',
                             help='register NUM of P-Reps for testing')
    prep_parser.add_argument('--get', type=address_type, metavar='ADDRESS', help='get P-Rep information')
    prep_parser.add_argument('--get-preps', action='store_true', help='get all P-Reps information')

    # register method
    setattr(cmd, 'prep', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    prep = PRep(tx_handler)
    if args.get or args.get_preps:
        try:
            if args.get:
                prep.print_prep_info(args.get)
            else:
                prep.print_preps_info()
            exit(0)
        except JSONRPCException as e:
            die(f'Error: {e}')
    if not args.keystore:
        die('Error: keystore should be specified')
    preps_num = args.register_test_preps if args.register_test_preps else 0
    if 0 < preps_num <= 100:
        if prep.is_test_endpoint(args.endpoint):
            prep.register_test_preps(args.keystore, preps_num)
            exit(0)
        else:
            die(f'Error: {args.endpoint} is not a test endpoint')
    if preps_num != 0:
        die(f'Error: invalid preps number')
