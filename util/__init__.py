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

import json
import sys

from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider


def die(message):
    print(message)
    sys.exit(-1)


def in_icx(value):
    return value / 10**18


def in_loop(value):
    return value * 10**18


def print_response(header, msg):
    if isinstance(msg, str):
        if msg.startswith("0x"):
            print(f'"{header}": "{msg}" ({int(msg, 16)})')
        else:
            print(f'"{header}": "{msg}"')
    elif isinstance(msg, dict):
        print(f'"{header}": {json.dumps(msg, indent=4)}')
    else:
        print(f'"{header}": "{msg}"')


def get_icon_service(endpoint):
    endpoint_map = {
        "mainnet": ['https://ctz.solidwallet.io', 0x1],
        "lisbon":  ['https://lisbon.net.solidwallet.io', 0x2],
        "berlin":  ['https://berlin.net.solidwallet.io', 0x7],
        "local":   ['http://localhost:9082', 0x3],
        "icon0":   ['http://localhost:9080', 0x3],
        "icon1":   ['http://localhost:9180', 0x101],
    }
    url, nid = endpoint_map.get(endpoint, [None, None])
    if not url:
        die(f'Error: supported endpoints: {list(endpoint_map.keys())}')
    print('[Endpoint]')
    print(f"{endpoint}: {url}/api/v3")
    return IconService(HTTPProvider(url, 3)), nid


def get_tracker_prefix(nid):
    tracker_map = {
        0x1: 'https://tracker.icon.community',
        0x2: 'https://tracker.lisbon.icon.community',
        0x3: 'http://localhost',
        0x7: 'https://tracker.berlin.icon.community',
    }
    return tracker_map.get(nid, None)
