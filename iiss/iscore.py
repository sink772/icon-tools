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

import getpass
import json

from iconsdk.exception import KeyStoreException
from iconsdk.wallet.wallet import KeyWallet

from score.chain import ChainScore
from util import die, in_icx, print_response, get_icon_service


def get_address_from_keystore(keystore):
    path = keystore.name
    with open(path, encoding='utf-8-sig') as f:
        keyfile: dict = json.load(f)
        return keyfile.get('address')


class IScore(object):

    def __init__(self, service):
        self._chain = ChainScore(service)

    def query(self, address):
        params = {
            "address": address
        }
        return self._chain.call("queryIScore", params)

    def claim(self, keystore):
        confirm = input('\n==> Are you sure you want to claim the IScore? (y/n) ')
        if confirm == 'y':
            try:
                passwd = getpass.getpass()
                wallet = KeyWallet.load(keystore.name, passwd)
                tx_hash = self._chain.invoke(wallet, "claimIScore")
                print(f'\n==> Success: https://tracker.icon.foundation/transaction/{tx_hash}')
            except KeyStoreException as e:
                die(e.message)

    def print_status(self, address):
        print('[IScore]')
        result = self.query(address)
        print_response(address, result)
        print('EstimatedICX =', in_icx(int(result['estimatedICX'], 16)))


def run(args):
    icon_service = get_icon_service(args.endpoint)
    iscore = IScore(icon_service)
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
        iscore.claim(args.keystore)
