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
from util import print_response, get_icon_service


class IScore(object):

    def __init__(self, service):
        self._chain = ChainScore(service)

    def query(self, address):
        params = {
            "address": address
        }
        return self._chain.call("queryIScore", params)

    def print_status(self, address):
        print('[IScore]')
        result = self.query(address)
        print_response(address, result)
        print('EstimatedICX =', int(result['estimatedICX'], 16) / 10**18)


def run(endpoint, address):
    icon_service = get_icon_service(endpoint)
    iscore = IScore(icon_service)
    iscore.print_status(address)
