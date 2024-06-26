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

from score import Score
from util.txhandler import TxHandler


class ChainScore(Score):
    ADDRESS = "cx0000000000000000000000000000000000000000"

    def __init__(self, tx_handler: TxHandler):
        super().__init__(tx_handler, self.ADDRESS)

    def queryIScore(self, address, height=None):
        return self.call("queryIScore", {"address": address}, height)

    def claimIScore(self, wallet):
        return self.invoke(wallet, "claimIScore")

    def getStake(self, address, height=None):
        return self.call("getStake", {"address": address}, height)

    def setStake(self, wallet, value):
        return self.invoke(wallet, "setStake", {"value": value})

    def getDelegation(self, address, height=None):
        return self.call("getDelegation", {"address": address}, height)

    def setDelegation(self, wallet, delegations: list):
        return self.invoke(wallet, "setDelegation", {"delegations": delegations})

    def getBond(self, address, height=None):
        return self.call("getBond", {"address": address}, height)

    def setBond(self, wallet, bonds: list):
        return self.invoke(wallet, "setBond", {"bonds": bonds})

    def setBonderList(self, wallet, addresses: list):
        return self.invoke(wallet, "setBonderList", {"bonderList": addresses})
