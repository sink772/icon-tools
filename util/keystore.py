# Copyright 2023 ICON Foundation
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

import getpass
import json

from iconsdk.exception import KeyStoreException
from iconsdk.wallet.wallet import KeyWallet

from util import die


class Keystore:

    def __init__(self, keystore, passwd):
        self._keystore = keystore
        self._passwd = passwd
        self._address = None

    @property
    def address(self):
        if not self._address:
            self._address = self.get_address_from_keystore()
        return self._address

    def get_address_from_keystore(self):
        if not self._keystore:
            die('Error: keystore should be specified')
        path = self._keystore.name
        with open(path, encoding='utf-8-sig') as f:
            keyfile: dict = json.load(f)
            return keyfile.get('address')

    def get_wallet(self):
        if not self._keystore:
            die('Error: keystore should be specified')
        try:
            passwd = self._passwd
            if passwd is None:
                passwd = getpass.getpass()
            return KeyWallet.load(self._keystore.name, passwd)
        except KeyStoreException as e:
            die(e.message)
