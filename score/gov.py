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

from score import Score
from util import die, print_response, get_icon_service, load_keystore


class Governance(Score):
    ADDRESS = "cx0000000000000000000000000000000000000001"

    def __init__(self, service, owner):
        super().__init__(service, self.ADDRESS)
        self._owner = owner

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
        step_price = self.get_step_price()
        print(f'"stepPrice": {step_price} ({int(step_price, 16)})')
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

    def accept_score(self, tx_hash):
        if not self._owner:
            die('Error: owner should be specified to invoke acceptScore')
        params = {
            "txHash": tx_hash
        }
        return self._invoke(self._owner, "acceptScore", params)


def run(args):
    icon_service = get_icon_service(args.endpoint)
    if args.keystore:
        owner = load_keystore(args.keystore)
    else:
        owner = None
    gov = Governance(icon_service, owner)
    gov.print_info()
    audit = gov.check_if_audit_enabled()
    if audit:
        print('Audit: enabled')
    else:
        print('Audit: disabled')
