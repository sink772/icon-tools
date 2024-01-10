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

import argparse
import re

from iconsdk.exception import JSONRPCException
from iconsdk.wallet.wallet import KeyWallet

from score.chain import ChainScore
from util import die, in_loop, print_response
from util.checks import address_type
from util.keystore import Keystore


class PRep(object):

    def __init__(self, tx_handler):
        self._tx_handler = tx_handler
        self._chain = ChainScore(tx_handler)

    def get_prep(self, address):
        return self._chain.call("getPRep", {"address": address})

    def get_preps(self):
        return self._chain.call("getPReps")

    def get_bond(self, address):
        return self._chain.call("getBond", {"address": address})

    def register_prep(self, wallet, name):
        _id = re.sub('\\s+', '_', name.lower())
        params = {
            "name": name,
            "country": "KOR",
            "city": "Seoul",
            "email": f"{_id}@example.com",
            "website": f"https://{_id}.example.com",
            "details": f"https://{_id}.example.com/details",
            "p2pEndpoint": f"{_id}.example.com:7100",
        }
        return self._chain.invoke(wallet, "registerPRep", params, value=in_loop(2000))

    def set_stake(self, wallet, amount):
        return self._chain.invoke(wallet, "setStake", {"value": amount})

    def set_delegation(self, wallet, amount):
        return self._chain.invoke(wallet, "setDelegation", {
            "delegations": [{
                "address": wallet.get_address(),
                "value": amount
            }]})

    def set_bond(self, wallet, amount):
        return self._chain.invoke(wallet, "setBond", {
            "bonds": [{
                "address": wallet.get_address(),
                "value": amount
            }]})

    def set_bonder_list(self, wallet, addresses: list):
        return self._chain.invoke(wallet, "setBonderList", {"bonderList": addresses})

    def print_prep_info(self, prep_addr):
        print_response('P-Rep Info', self.get_prep(prep_addr))

    def print_preps_info(self):
        print_response('P-Reps Info', self.get_preps())

    @staticmethod
    def is_test_endpoint(endpoint):
        return endpoint in ('local', 'gochain', 'icon0', 'icon1')

    def get_minimum_delegation(self):
        min_delegate_value = self._tx_handler.total_supply() // 500
        print(f"min_delegate_value = ({min_delegate_value}, {min_delegate_value // 10 ** 18})")
        return min_delegate_value

    def register_prep_by_keystore(self, god_keystore, prep_keystore):
        god_wallet = god_keystore.get_wallet()
        wallet = prep_keystore.get_wallet()
        # transfer the required icx from the god wallet
        stake_amount = self.get_minimum_delegation()
        bond_amount = in_loop(100_000)
        tx_hash = self._tx_handler.transfer(god_wallet, wallet.get_address(), stake_amount * 2)
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"registerPRep")
        name = f"node_{wallet.get_address()[:16]}"
        tx_hash = self.register_prep(wallet, name)
        print(f"  [{wallet.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"setStake")
        tx_hash = self.set_stake(wallet, stake_amount + bond_amount)
        print(f"  [{wallet.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"setDelegation")
        tx_hash = self.set_delegation(wallet, (stake_amount - bond_amount))
        print(f"  [{wallet.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"setBond")
        tx_hash = self.set_bonder_list(wallet, [wallet.get_address()])
        self._tx_handler.ensure_tx_result(tx_hash)
        tx_hash = self.set_bond(wallet, bond_amount)
        print(f"  [{wallet.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

    def register_test_preps(self, keystore, preps_num):
        god_wallet = keystore.get_wallet()
        min_delegate_value = self.get_minimum_delegation()
        transfer_value = in_loop(105_000)
        # add god wallet as the 1st prep
        test_preps = [god_wallet]
        delegates = [min_delegate_value]
        tx_hash = None
        for i in range(preps_num - 1):
            wallet = KeyWallet.create()
            test_preps.append(wallet)
            delegates.append(in_loop(100_000))
            tx_hash = self._tx_handler.transfer(god_wallet, wallet.get_address(), transfer_value)
        if tx_hash:
            self._tx_handler.ensure_tx_result(tx_hash)

        print(f"registerPRep")
        for prep in test_preps:
            name = f"node_{prep.get_address()}"
            tx_hash = self.register_prep(prep, name)
            print(f"  [{prep.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"setStake")
        for i, prep in enumerate(test_preps):
            tx_hash = self.set_stake(prep, delegates[i])
            print(f"  [{prep.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"setDelegation")
        for i, prep in enumerate(test_preps):
            tx_hash = self.set_delegation(prep, delegates[i])
            print(f"  [{prep.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

        print(f"setBond")
        main_prep = test_preps[0]
        bond_amount = in_loop(100_000)
        self.set_stake(main_prep, min_delegate_value + bond_amount)
        tx_hash = self.set_bonder_list(main_prep, [main_prep.get_address()])
        self._tx_handler.ensure_tx_result(tx_hash)
        tx_hash = self.set_bond(main_prep, bond_amount)
        print(f"  [{main_prep.get_address()}] tx_hash={tx_hash}")
        self._tx_handler.ensure_tx_result(tx_hash)

    def do_self_bond(self, keystore, amount):
        bond_info = self.get_bond(keystore.address)
        print_response('Bond Info', bond_info)
        print('NewBond =', in_loop(amount), f"({amount} ICX)")
        confirm = input(f'\n==> Are you sure you want to set new bond? (y/n) ')
        if confirm == 'y':
            wallet = keystore.get_wallet()
            tx_hash = self.set_bond(wallet, in_loop(amount))
            self._tx_handler.ensure_tx_result(tx_hash, True)


def add_parser(cmd, subparsers):
    prep_parser = subparsers.add_parser('prep', help='P-Rep management')
    prep_parser.add_argument('--register-prep', type=argparse.FileType('r'), metavar='KEYSTORE',
                             help='register P-Rep by KEYSTORE')
    prep_parser.add_argument('--register-test-preps', type=int, metavar='NUM',
                             help='register NUM of P-Reps for testing')
    prep_parser.add_argument('--self-bond', type=int, metavar='AMOUNT', help='the amount of self-bond in ICX')
    prep_parser.add_argument('--get', type=address_type, metavar='ADDRESS', help='get P-Rep information')
    prep_parser.add_argument('--get-preps', action='store_true', help='get all P-Reps information')

    # register method
    setattr(cmd, 'prep', run)


def run(args):
    prep = PRep(args.txhandler)
    if args.get or args.get_preps:
        try:
            if args.get:
                prep.print_prep_info(args.get)
            else:
                prep.print_preps_info()
            exit(0)
        except JSONRPCException as e:
            die(f'Error: {e}')
    if args.register_prep:
        prep_keystore = Keystore(args.register_prep, 'gochain')
        prep.register_prep_by_keystore(args.keystore, prep_keystore)
        exit(0)
    elif args.self_bond:
        prep.do_self_bond(args.keystore, args.self_bond)
        exit(0)
    preps_num = args.register_test_preps if args.register_test_preps else 0
    if 0 < preps_num <= 100:
        if prep.is_test_endpoint(args.endpoint):
            prep.register_test_preps(args.keystore, preps_num)
            exit(0)
        else:
            die(f'Error: {args.endpoint} is not a test endpoint')
    if preps_num != 0:
        die(f'Error: invalid preps number')
