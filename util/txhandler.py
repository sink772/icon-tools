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

from time import sleep

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import (
    CallTransactionBuilder, DeployTransactionBuilder, TransactionBuilder
)
from iconsdk.signed_transaction import SignedTransaction

from . import die, print_response, get_tracker_prefix


class TxHandler:
    SYSTEM_ADDRESS = "cx0000000000000000000000000000000000000000"

    def __init__(self, service, nid):
        self._icon_service = service
        self._nid = nid

    @property
    def icon_service(self):
        return self._icon_service

    @property
    def nid(self):
        return self._nid

    def _send_transaction(self, transaction, wallet, limit):
        if limit is not None:
            signed_tx = SignedTransaction(transaction, wallet, limit)
        else:
            estimated_step = self._icon_service.estimate_step(transaction)
            estimated_step += 100_000  # add some margin
            signed_tx = SignedTransaction(transaction, wallet, estimated_step)
        return self._icon_service.send_transaction(signed_tx)

    def _deploy(self, wallet, to, content, params, limit):
        transaction = DeployTransactionBuilder() \
            .from_(wallet.get_address()) \
            .to(to) \
            .nid(self._nid) \
            .content_type("application/zip") \
            .content(content) \
            .params(params) \
            .build()
        return self._send_transaction(transaction, wallet, limit)

    def install(self, wallet, content, params=None, limit=None):
        return self._deploy(wallet, self.SYSTEM_ADDRESS, content, params, limit)

    def update(self, wallet, to, content, params=None, limit=None):
        return self._deploy(wallet, to, content, params, limit)

    def call(self, to, method, params=None, height=None):
        _call = CallBuilder() \
            .to(to) \
            .method(method) \
            .params(params) \
            .height(height) \
            .build()
        return self._icon_service.call(_call)

    def invoke(self, wallet, to, method, params, value=0, limit=None):
        transaction = CallTransactionBuilder() \
            .from_(wallet.get_address()) \
            .to(to) \
            .nid(self._nid) \
            .value(value) \
            .method(method) \
            .params(params) \
            .build()
        return self._send_transaction(transaction, wallet, limit)

    def transfer(self, wallet, to, amount, limit=100000):
        transaction = TransactionBuilder() \
            .from_(wallet.get_address()) \
            .to(to) \
            .nid(self._nid) \
            .value(amount) \
            .build()
        return self._send_transaction(transaction, wallet, limit)

    def get_balance(self, address, height=None):
        return self._icon_service.get_balance(address, height)

    def total_supply(self, height=None):
        return self._icon_service.get_total_supply(height)

    def get_network_info(self):
        return self._icon_service.get_network_info()

    def get_score_status(self, address, height=None):
        return self._icon_service.get_score_status(address, height)

    def get_tx_result(self, tx_hash):
        return self._icon_service.get_transaction_result(tx_hash)

    def get_tx_by_hash(self, tx_hash):
        return self._icon_service.get_transaction(tx_hash, True)

    def ensure_tx_result(self, tx_hash, verbose=False):
        if verbose:
            prefix = get_tracker_prefix(self.nid)
            if prefix is not None:
                print(f'\n==> {prefix}/transaction/{tx_hash}')
        count = 5
        while True:
            result = self._icon_service.get_transaction_result(tx_hash, True)
            if 'error' in result:
                count -= 1
                if count <= 0:
                    print_response("Response", result['error'])
                    die('Error: failed to get transaction result')
                sleep(2)
            elif 'result' in result:
                result = result['result']
                if verbose:
                    print_response("Result", result)
                if result['status'] != '0x1':
                    die('Error: transaction failed')
                return result
            else:
                print_response("Response", result)
                die(f'Error: unknown response')
