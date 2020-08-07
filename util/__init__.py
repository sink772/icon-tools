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

import json
from time import sleep

from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction


def print_response(header, msg):
    print(f'"{header}": {json.dumps(msg, indent=4)}')


def get_icon_service(endpoint):
    endpoint_map = {
        "mainnet": 'https://ctz.solidwallet.io',
        "testnet": 'https://test-ctz.solidwallet.io',
        "bicon": 'https://bicon.net.solidwallet.io',
        "local": 'http://localhost:9000',
    }
    url = endpoint_map.get(endpoint, endpoint)
    print('[Endpoint]')
    print(f"{endpoint}: {url}/api/v3\n")
    return IconService(HTTPProvider(f"{url}/api/v3"))


class TxHandler:
    ZERO_ADDRESS = "cx0000000000000000000000000000000000000000"

    def __init__(self, service):
        self._icon_service = service

    def _deploy(self, owner, to, content, params, limit):
        transaction = DeployTransactionBuilder() \
            .from_(owner.get_address()) \
            .to(to) \
            .step_limit(limit) \
            .version(3) \
            .nid(3) \
            .content_type("application/zip") \
            .content(content) \
            .params(params) \
            .build()
        return self._icon_service.send_transaction(SignedTransaction(transaction, owner))

    def install(self, owner, content, params=None, limit=0x50000000):
        return self._deploy(owner, self.ZERO_ADDRESS, content, params, limit)

    def update(self, owner, to, content, params=None, limit=0x70000000):
        return self._deploy(owner, to, content, params, limit)

    def invoke(self, owner, to, method, params, limit=0x10000000):
        transaction = CallTransactionBuilder() \
            .from_(owner.get_address()) \
            .to(to) \
            .step_limit(limit) \
            .nid(3) \
            .method(method) \
            .params(params) \
            .build()
        return self._icon_service.send_transaction(SignedTransaction(transaction, owner))

    def get_tx_result(self, tx_hash):
        while True:
            try:
                tx_result = self._icon_service.get_transaction_result(tx_hash)
                return tx_result
            except JSONRPCException as e:
                print(e.message)
                sleep(2)
