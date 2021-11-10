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

import getpass
import json
import sys

from iconsdk.exception import KeyStoreException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.wallet.wallet import KeyWallet


def die(message):
    print(message)
    sys.exit(-1)


def in_icx(value):
    return value / 10**18


def in_loop(value):
    return value * 10**18


def print_response(header, msg):
    print(f'"{header}": {json.dumps(msg, indent=4)}')


def get_icon_service(endpoint):
    endpoint_map = {
        "mainnet": ['https://ctz.solidwallet.io', 0x1, 'gl'],
        "sejong":  ['https://sejong.net.solidwallet.io', 0x53, 'gl'],
        "btpnet":  ['https://btp.net.solidwallet.io', 0x42, 'gl'],
        "gochain": ['http://localhost:9082', 0x3, 'gl'],
    }
    url, nid, eng = endpoint_map.get(endpoint, [endpoint, 0x3, 'gl'])
    print('[Endpoint]')
    print(f"{endpoint}: {url}/api/v3")
    return IconService(HTTPProvider(url, 3)), nid, eng


def get_address_from_keystore(keystore):
    path = keystore.name
    with open(path, encoding='utf-8-sig') as f:
        keyfile: dict = json.load(f)
        return keyfile.get('address')


def load_keystore(keystore, passwd=None):
    try:
        if passwd is None:
            passwd = getpass.getpass()
        return KeyWallet.load(keystore.name, passwd)
    except KeyStoreException as e:
        die(e.message)
