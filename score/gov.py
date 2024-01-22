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

import json

from score import Score
from score.chain import ChainScore
from util import die, print_response
from util.checks import address_type, tx_hash_type


class Governance(Score):
    GOV_ADDRESS = "cx0000000000000000000000000000000000000001"

    def __init__(self, tx_handler):
        super().__init__(tx_handler, self.GOV_ADDRESS)

    def gov_call(self, method, params=None):
        return super().call(method, params)

    # override call implementation
    def call(self, method, params=None, height=None):
        return self._tx_handler.call(ChainScore.ADDRESS, method, params)

    def get_version(self):
        return self.gov_call("getVersion")

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
        print_response("revision", self.get_revision())
        print_response("stepPrice", self.get_step_price())
        max_step_limits = {
            "invoke": self.get_max_step_limit("invoke"),
            "query": self.get_max_step_limit("query")
        }
        print_response('maxStepLimits', max_step_limits)
        print_response('stepCosts', self.get_step_costs())
        print_response('serviceConfig', self.get_service_config())

    def check_if_audit_enabled(self):
        service_config = self.get_service_config()
        return int(service_config, 16) & 0x2 != 0

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

    def accept_score(self, wallet, tx_hash):
        params = {
            "txHash": tx_hash
        }
        res_hash = self.invoke(wallet, "acceptScore", params, limit=1_000_000)
        self._tx_handler.ensure_tx_result(res_hash, True)

    def reject_score(self, wallet, tx_hash, reason):
        if not reason:
            die('Error: reason should be specified for rejecting')
        params = {
            "txHash": tx_hash,
            "reason": reason
        }
        res_hash = self.invoke(wallet, "rejectScore", params, limit=500_000)
        self._tx_handler.ensure_tx_result(res_hash, True)

    def process_batch(self, wallet, contracts, accept, reason):
        if accept:
            action = 'accept'
        else:
            action = 'reject'
        for name, score_address in contracts.items():
            print(f'\n>>> {name}: {score_address}')
            status = self.get_score_status(score_address)
            print_response('status', status)
            if reason:
                print(f'\"reason\": \"{reason}\"')
            if status['next']['status'] == 'pending':
                deploy_hash = status['next']['deployTxHash']
                confirm = input(f'\n==> Are you sure you want to {action} this score? (y/n) ')
                if confirm == 'y':
                    if accept:
                        self.accept_score(wallet, deploy_hash)
                    else:
                        self.reject_score(wallet, deploy_hash, reason)


def add_parser(cmd, subparsers):
    gov_parser = subparsers.add_parser('gov', help='Check governance status')
    gov_parser.add_argument('--score-status', type=address_type, metavar='ADDRESS',
                            help='show the given SCORE status')
    gov_parser.add_argument('--accept-score', type=tx_hash_type, metavar='TX_HASH',
                            help='accept the given deploy transaction')
    gov_parser.add_argument('--accept-batch', type=str, metavar='CONTRACTS_JSON',
                            help='accept multiple deploy transactions')
    gov_parser.add_argument('--reject-score', type=tx_hash_type, metavar='TX_HASH',
                            help='reject the given deploy transaction')
    gov_parser.add_argument('--reject-batch', type=str, metavar='CONTRACTS_JSON',
                            help='reject multiple deploy transactions')
    gov_parser.add_argument('--reason', type=str, help='reason for rejecting')

    # register method
    setattr(cmd, 'gov', run)


def run(args):
    gov = Governance(args.txhandler)
    tx_hash = args.accept_score if args.accept_score else args.reject_score
    json_file = args.accept_batch if args.accept_batch else args.reject_batch
    if args.score_status:
        status = gov.get_score_status(args.score_status)
        print_response('status', status)
    elif tx_hash:
        if gov.check_if_tx_pending(tx_hash):
            if args.reject_score:
                if args.reason:
                    reject_reason = args.reason
                else:
                    reason = input('\n==> Reason: ')
                    if len(reason) > 0:
                        reject_reason = reason
                print(f'\"reason\": \"{reject_reason}\"')
            wallet = args.keystore.get_wallet()
            if args.accept_score:
                gov.accept_score(wallet, tx_hash)
            else:
                gov.reject_score(wallet, tx_hash, reject_reason)
    elif json_file:
        wallet = args.keystore.get_wallet()
        with open(json_file, "r") as f:
            contracts: dict = json.loads(f.read())
        gov.process_batch(wallet, contracts, args.accept_batch, args.reason)
    else:
        gov.print_info()
        audit = gov.check_if_audit_enabled()
        if audit:
            print('Audit: enabled')
        else:
            print('Audit: disabled')
