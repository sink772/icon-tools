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

import json
from datetime import datetime

import requests

from score.gov import Governance
from util import die, get_icon_service, get_tracker_prefix, print_response
from util.txhandler import TxHandler

STATUS_OK = 200


class Audit(object):

    def __init__(self, tx_handler: TxHandler, keystore, endpoint):
        self._tx_handler = tx_handler
        self._keystore = keystore
        self._endpoint = endpoint
        self._method_handler = {
            'a': self.accept_score,
            'r': self.reject_score,
            'd': self.download_contract,
            's': self.get_score_status,
            'v': self.verify_contract
        }

    def get_pending_list(self, prefix):
        ignore_list = []
        if self._endpoint == 'mainnet':
            try:
                with open(".audit_ignore_list", "r") as f:
                    ignore_list = json.loads(f.read())
            except FileNotFoundError:
                pass
        url = f"{prefix}/v3/contract/pendingList?count=25"
        res = requests.get(url)
        ret = list()
        if STATUS_OK == res.status_code:
            content = json.loads(res.content)
            data = content['data']
            count = len(data)
            for i in range(count):
                item = data[i]
                address = item['contractAddr']
                if address not in ignore_list:
                    ret.append(item)
        return ret

    @staticmethod
    def get_contract_list(prefix):
        list_size, page = 0, 0
        count = 90
        ret = list()
        while list_size == 0 or (page * count) < list_size:
            page += 1
            url = f"{prefix}/v3/contract/list?page={page}&count={count}&status=1"
            res = requests.get(url)
            if STATUS_OK == res.status_code:
                content = json.loads(res.content)
                data = content['data']
                list_size = content['listSize']
                ret.extend(data)
        print("listSize =", list_size)
        return ret

    def accept_score(self, contract):
        tx_hash = contract['createTx']
        gov = Governance(self._tx_handler)
        if gov.check_if_tx_pending(tx_hash):
            wallet = self._keystore.get_wallet()
            gov.accept_score(wallet, tx_hash)
        return False

    def reject_score(self, contract):
        tx_hash = contract['createTx']
        reason = input('\n==> Reason: ')
        if len(reason) > 0:
            gov = Governance(self._tx_handler)
            if gov.check_if_tx_pending(tx_hash):
                print(f'\"reason\": \"{reason}\"')
                wallet = self._keystore.get_wallet()
                gov.reject_score(wallet, tx_hash, reason)
        return False

    def get_score_status(self, contract):
        address = contract['contractAddr']
        gov = Governance(self._tx_handler)
        print_response('status', gov.get_score_status(address))
        return True

    def download_contract(self, contract):
        create_tx = contract['createTx']
        result = self._tx_handler.get_tx_by_hash(create_tx)
        if 'result' in result:
            raw_tx = result['result']
            content = bytes.fromhex(raw_tx['data']['content'][2:])
            filename = f"{contract['contractAddr']}_{contract['version']}.zip"
            with open(filename, 'wb') as dest:
                dest.write(content)
            print('Downloaded', filename)
            return True
        else:
            die('Error: failed to get transaction data')

    def verify_contract(self, contract):
        url = "http://localhost:8888/v2/score/verify"
        headers = {'Content-Type': 'application/json'}
        _data = {
            "deployTxHash": contract['createTx'],
            "network": self._endpoint
        }
        try:
            res = requests.post(url, headers=headers, data=json.dumps(_data))
            print(f'status={res.status_code}, content={res.content}')
            return True
        except requests.ConnectionError as e:
            die(f'Error: {e}')

    def run(self, args):
        prefix = get_tracker_prefix(self._tx_handler.nid)
        if prefix is None:
            die('Cannot find tracker server')
        if args.dump_java or args.dump_contract:
            contracts = self.get_contract_list(prefix)
        else:
            contracts = self.get_pending_list(prefix)
        if len(contracts) == 0:
            die('No pending SCOREs')

        if args.dump_contract:
            print("count =", len(contracts))
            results = {}
            for i, item in enumerate(contracts):
                verified_data = item['verifiedDate']
                name = item['contractName']
                address = item['address']
                results[address] = f'{name}, {verified_data}'
            print(json.dumps(results))
        elif args.dump_java:
            print("count =", len(contracts))
            self.print_java_contracts(contracts)
        elif args.export:
            print('{')
            for i, item in reversed(list(enumerate(contracts))):
                version = item['version']
                name = item['contractName']
                address = item['contractAddr']
                if i > 0:
                    print(f'    "{i}:{version}:{name}": "{address}",')
                else:
                    print(f'    "{i}:{version}:{name}": "{address}"')
            print('}')
        else:
            self.print_pending_contracts(contracts)
            while args.interactive:
                try:
                    num = input('\n==> Select: ')
                    if 0 <= int(num) < len(contracts):
                        action = input('Action ([a]ccept, [r]eject, [s]tatus, [d]ownload, [v]erify: ')
                        if len(action) == 1 and action in "ardvs":
                            _handler = self._method_handler[action]
                            if _handler(contracts[int(num)]):
                                continue
                            break
                        raise ValueError(f'Error: invalid action: {action}')
                    else:
                        raise ValueError(f'Error: invalid input: {num}')
                except KeyboardInterrupt:
                    die('exit')
                except ValueError as e:
                    print(e.__str__())
                    self.print_pending_contracts(contracts)
                    continue

    @staticmethod
    def print_pending_contracts(contracts):
        for i, item in enumerate(contracts):
            version = item['version']
            name = item['contractName']
            create_tx = item['createTx']
            address = item['contractAddr']
            create_date = item['createDate'].split('.')[0]
            print(f'[{i}] {version} {name}, {create_tx} - {address} - {create_date}')

    def print_java_contracts(self, contracts):
        results = {}
        gov = Governance(self._tx_handler)
        for i, item in enumerate(contracts):
            verified_data = item['verifiedDate']
            try:
                if datetime.fromisoformat(verified_data).year >= 2022:
                    name = item['contractName']
                    address = item['address']
                    status = gov.get_score_status(address)
                    current = status['current']
                    if current['deployTxHash'] == current['auditTxHash']:
                        results[address] = f'{name}, {verified_data}'
            except ValueError:
                print("[ValueError]", item)

        print(json.dumps(results))


def add_parser(cmd, subparsers):
    audit_parser = subparsers.add_parser('audit', help='Perform audit operations')
    audit_parser.add_argument('--interactive', action='store_true', help='enter to interactive mode')
    audit_parser.add_argument('--export', action='store_true', help='export pending list as json')
    audit_parser.add_argument('--dump-java', action='store_true', help='dump Java contract list')
    audit_parser.add_argument('--dump-contract', action='store_true', help='dump active contract list')

    # register method
    setattr(cmd, 'audit', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    audit = Audit(tx_handler, args.keystore, args.endpoint)
    audit.run(args)
