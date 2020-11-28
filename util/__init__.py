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
import sys
from time import sleep

from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder, TransactionBuilder
from iconsdk.exception import JSONRPCException, KeyStoreException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet


def die(message):
    print(message)
    sys.exit(-1)


def in_icx(value):
    return value / 10**18


def in_loop(value):
    return value * 10**18


def print_response(header, msg):
    print(f'"{header}": {json.dumps(msg, indent=4)}')


def get_icon_service(endpoint):
    endpoint_map = {
        "mainnet": 'https://ctz.solidwallet.io',
        "testnet": 'https://test-ctz.solidwallet.io',
        "bicon": 'https://bicon.net.solidwallet.io',
        "gangnam": 'https://gicon.net.solidwallet.io',
        "local": 'http://localhost:9000',
    }
    url = endpoint_map.get(endpoint, endpoint)
    print('[Endpoint]')
    print(f"{endpoint}: {url}/api/v3\n")
    return IconService(HTTPProvider(url, 3))


def get_address_from_keystore(keystore):
    path = keystore.name
    with open(path, encoding='utf-8-sig') as f:
        keyfile: dict = json.load(f)
        return keyfile.get('address')


def load_keystore(keystore, passwd=None):
    try:
        if passwd is None:
            passwd = getpass.getpass()
        return KeyWallet.load(keystore.name, passwd)
    except KeyStoreException as e:
        die(e.message)


class TxHandler:
    ZERO_ADDRESS = "cx0000000000000000000000000000000000000000"

    def __init__(self, service):
        self._icon_service = service

    def _deploy(self, wallet, to, content, params, limit, nid=1):
        transaction = DeployTransactionBuilder() \
            .from_(wallet.get_address()) \
            .to(to) \
            .step_limit(limit) \
            .version(3) \
            .nid(nid) \
            .content_type("application/zip") \
            .content(content) \
            .params(params) \
            .build()
        return self._icon_service.send_transaction(SignedTransaction(transaction, wallet))

    def install(self, wallet, content, params=None, limit=0x50000000):
        return self._deploy(wallet, self.ZERO_ADDRESS, content, params, limit)

    def update(self, wallet, to, content, params=None, limit=0x70000000):
        return self._deploy(wallet, to, content, params, limit)

    def _send_transaction(self, transaction, wallet, limit):
        if limit is not None:
            signed_tx = SignedTransaction(transaction, wallet, limit)
        else:
            estimated_step = self._icon_service.estimate_step(transaction)
            signed_tx = SignedTransaction(transaction, wallet, estimated_step)
        return self._icon_service.send_transaction(signed_tx)

    def invoke(self, wallet, to, method, params, nid=1, limit=None):
        transaction = CallTransactionBuilder() \
            .from_(wallet.get_address()) \
            .to(to) \
            .nid(nid) \
            .method(method) \
            .params(params) \
            .build()
        return self._send_transaction(transaction, wallet, limit)

    def transfer(self, wallet, to, amount, nid=1, limit=None):
        transaction = TransactionBuilder() \
            .from_(wallet.get_address()) \
            .to(to) \
            .value(amount) \
            .nid(nid) \
            .build()
        return self._send_transaction(transaction, wallet, limit)

    def get_tx_result(self, tx_hash):
        while True:
            try:
                tx_result = self._icon_service.get_transaction_result(tx_hash)
                return tx_result
            except JSONRPCException as e:
                print(e.message)
                sleep(2)
