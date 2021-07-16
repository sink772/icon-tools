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
import requests

from score.gov import Governance
from util import die, get_icon_service, load_keystore
from util.txhandler import TxHandler

STATUS_OK = 200
IGNORED_LIST = [
    "cx13f08df7106ae462c8358066e6d47bb68d995b6d",
    "cx0000000000000000000000000000000000000001"
]


class Audit(object):

    def __init__(self, tx_handler: TxHandler, keystore):
        self._tx_handler = tx_handler
        self._keystore = keystore
        self._method_handler = {
            'a': self.accept_score,
            'r': self.reject_score,
            'd': self.download_contract,
            'v': self.verify_contract
        }

    @staticmethod
    def get_pending_list():
        url = "https://tracker.icon.foundation/v3/contract/pendingList"
        res = requests.get(url)
        ret = list()
        if STATUS_OK == res.status_code:
            content = json.loads(res.content)
            data = content['data']
            count = len(data)
            for i in range(count):
                item = data[i]
                address = item['contractAddr']
                if address not in IGNORED_LIST:
                    ret.append(item)
        return ret

    def accept_score(self, contract):
        if not self._keystore:
            die('Error: keystore should be specified')
        tx_hash = contract['createTx']
        gov = Governance(self._tx_handler)
        if gov.check_if_tx_pending(tx_hash):
            wallet = load_keystore(self._keystore)
            gov.accept_score(wallet, tx_hash)
        return False

    def reject_score(self, contract):
        if not self._keystore:
            die('Error: keystore should be specified')
        tx_hash = contract['createTx']
        reason = input('\n==> Reason: ')
        if len(reason) > 0:
            gov = Governance(self._tx_handler)
            if gov.check_if_tx_pending(tx_hash):
                print(f'\"reason\": \"{reason}\"')
                wallet = load_keystore(self._keystore)
                gov.reject_score(wallet, tx_hash, reason)
        return False

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
            "deployTxHash": contract['createTx']
        }
        try:
            res = requests.post(url, headers=headers, data=json.dumps(_data))
            print(f'status={res.status_code}, content={res.content}')
            return True
        except requests.ConnectionError as e:
            die(f'Error: {e}')

    def run(self, args):
        contracts = self.get_pending_list()
        if len(contracts) == 0:
            die('No pending SCOREs')

        if args.export:
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
            return

        for i, item in enumerate(contracts):
            version = item['version']
            name = item['contractName']
            create_tx = item['createTx']
            address = item['contractAddr']
            create_date = item['createDate'].split('.')[0]
            print(f'[{i}] {version} {name}, {create_tx} - {address} - {create_date}')

        while args.interactive:
            try:
                num = input('\n==> Select: ')
                if 0 <= int(num) < len(contracts):
                    action = input('Action ([a]ccept, [r]eject, [d]ownload, [v]erify: ')
                    if len(action) == 1 and action in "ardv":
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
                continue


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    audit = Audit(tx_handler, args.keystore)
    audit.run(args)
