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
from util.txhandler import TxHandler


class Governance(Score):
    ADDRESS = "cx0000000000000000000000000000000000000001"

    def __init__(self, tx_handler: TxHandler):
        super().__init__(tx_handler, self.ADDRESS)

    def get_version(self):
        return self.call("getVersion")

    def get_revision(self):
        return self.call("getRevision")

    def get_step_price(self):
        return self.call("getStepPrice")

    def get_max_step_limit(self, ctype):
        params = {
            "contextType": ctype
        }
        return self.call("getMaxStepLimit", params)

    def get_step_costs(self):
        return self.call("getStepCosts")

    def get_service_config(self):
        return self.call("getServiceConfig")

    def get_score_status(self, address):
        params = {
            "address": address
        }
        return self.call("getScoreStatus", params)

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

    def check_if_tx_pending(self, tx_hash):
        result = self._tx_handler.get_tx_result(tx_hash)
        try:
            score_address = result['scoreAddress']
            status = self.get_score_status(score_address)
            print_response('status', status)
            if status['next']['status'] == 'pending' and \
                    status['next']['deployTxHash'] == tx_hash:
                return True
            else:
                die(f'Error: invalid txHash or no pending tx')
        except KeyError as e:
            if str(e) == "'scoreAddress'":
                msg = 'not a deploy transaction'
            elif str(e) == "'next'":
                msg = 'already accepted or rejected'
            else:
                msg = str(e)
            die(f'Error: {msg}')
        return False

    def accept_score(self, keystore, tx_hash):
        if not keystore:
            die('Error: keystore should be specified to invoke acceptScore')
        owner = load_keystore(keystore)
        params = {
            "txHash": tx_hash
        }
        res_hash = self.invoke(owner, "acceptScore", params, limit=500_000)
        self._tx_handler.ensure_tx_result(res_hash, True)

    def reject_score(self, keystore, tx_hash, reason):
        if not reason:
            die('Error: reason should be specified for rejecting')
        if not keystore:
            die('Error: keystore should be specified to invoke rejectScore')
        owner = load_keystore(keystore)
        params = {
            "txHash": tx_hash,
            "reason": reason
        }
        res_hash = self.invoke(owner, "rejectScore", params, limit=300_000)
        self._tx_handler.ensure_tx_result(res_hash, True)


def run(args):
    icon_service, nid = get_icon_service(args.endpoint)
    tx_handler = TxHandler(icon_service, nid)
    gov = Governance(tx_handler)
    if args.accept_score:
        tx_hash = args.accept_score
        if gov.check_if_tx_pending(tx_hash):
            gov.accept_score(args.keystore, tx_hash)
    elif args.reject_score:
        tx_hash = args.reject_score
        if gov.check_if_tx_pending(tx_hash):
            gov.reject_score(args.keystore, tx_hash, args.reason)
    else:
        gov.print_info()
        audit = gov.check_if_audit_enabled()
        if audit:
            print('Audit: enabled')
        else:
            print('Audit: disabled')
