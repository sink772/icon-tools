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

from iconsdk.builder.call_builder import CallBuilder

from util import TxHandler


class Score:

    def __init__(self, service, address):
        self._icon_service = service
        self._address = address
        self._tx_handler = TxHandler(service)

    def _call(self, method, params=None):
        call = CallBuilder() \
            .to(self._address) \
            .method(method) \
            .params(params) \
            .build()
        return self._icon_service.call(call)

    def _invoke(self, wallet, method, params=None):
        return self._tx_handler.invoke(wallet, self._address, method, params)
