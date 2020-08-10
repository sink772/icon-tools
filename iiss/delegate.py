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

from score.chain import ChainScore
from util import die, in_icx, in_loop, print_response, get_icon_service, get_address_from_keystore


class Delegate(object):

    def __init__(self, service):
        self._chain = ChainScore(service)
        self._icon_service = service

    def query(self, address):
        params = {
            "address": address
        }
        return self._chain.call("getDelegation", params)

    def get_total_delegated(self, address):
        result = self.query(address)
        return int(result['totalDelegated'], 16)

    @staticmethod
    def print_status(address, result):
        print('[Delegation]')
        print_response(address, result)

    def ask_to_set(self, address, keystore):
        print('ask_to_set')
