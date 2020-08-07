# Copyright 2019 ICON Foundation
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
import sys

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.wallet.wallet import KeyWallet

from util import TxHandler, print_response


class Governance:
    ADDRESS = "cx0000000000000000000000000000000000000001"

    def __init__(self, service, owner):
        self._icon_service = service
        self._owner = owner

    def _call(self, method, params=None):
        call = CallBuilder() \
            .to(self.ADDRESS) \
            .method(method) \
            .params(params) \
            .build()
        return self._icon_service.call(call)

    def get_version(self):
        return self._call("getVersion")

    def get_revision(self):
        return self._call("getRevision")

    def get_step_price(self):
        return self._call("getStepPrice")

    def get_max_step_limit(self, ctype):
        params = {
            "contextType": ctype
        }
        return self._call("getMaxStepLimit", params)

    def get_step_costs(self):
        return self._call("getStepCosts")

    def get_service_config(self):
        return self._call("getServiceConfig")

    def get_score_status(self, address):
        params = {
            "address": address
        }
        return self._call("getScoreStatus", params)

    def print_info(self):
        print('[Governance]')
        print_response('version', self.get_version())
        print_response('revision', self.get_revision())
        print_response('stepPrice', self.get_step_price())
        max_step_limits = {
            "invoke": self.get_max_step_limit("invoke"),
            "query": self.get_max_step_limit("query")
        }
        print_response('stepLimit', max_step_limits)
        print_response('stepCosts', self.get_step_costs())
        print_response('serviceConfig', self.get_service_config())

    def check_if_audit_enabled(self):
        service_config = self.get_service_config()
        if service_config.get('AUDIT', 0) == '0x1':
            return True
        else:
            return False

    def send_accept_score(self, handler: TxHandler, tx_hash):
        params = {
            "txHash": tx_hash
        }
        return handler.invoke(self._owner, self.ADDRESS, "acceptScore", params)


def run(endpoint: str):
    endpoint_map = {
        "local": 'http://localhost:9000',
        "mainnet": 'https://ctz.solidwallet.io',
        "testnet": 'https://test-ctz.solidwallet.io',
        "bicon": 'https://bicon.net.solidwallet.io',
    }
    url = endpoint_map.get(endpoint, endpoint)
    print('[Endpoint]')
    print(f"{endpoint}: {url}/api/v3\n")

    icon_service = IconService(HTTPProvider(f"{url}/api/v3"))
    owner_wallet = KeyWallet.load("./conf/keystore_test1", "test1_Account")

    gov = Governance(icon_service, owner_wallet)
    gov.print_info()
    audit = gov.check_if_audit_enabled()
    if audit:
        print('Audit: enabled')
    else:
        print('Audit: disabled')


def main():
    parser = argparse.ArgumentParser(prog='check_gov', description='Check governance status')
    parser.add_argument('endpoint', type=str, nargs='?', default="mainnet", help='an endpoint for connection')
    args = parser.parse_args()
    run(args.endpoint)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("exit")
