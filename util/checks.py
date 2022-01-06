# Copyright 2022 ICON Foundation
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

import argparse


def address_type(string):
    if isinstance(string, str) and len(string) == 42:
        prefix = string[:2]
        if prefix == "hx" or prefix == "cx":
            body_bytes = bytes.fromhex(string[2:])
            body = body_bytes.hex()
            if str(string) == prefix + body:
                return string
    raise argparse.ArgumentTypeError(f"Invalid address: '{string}'")


def tx_hash_type(string):
    if isinstance(string, str) and len(string) == 66:
        prefix = string[:2]
        if prefix == "0x":
            hash_bytes = bytes.fromhex(string[2:])
            tx_hash = hash_bytes.hex()
            if str(string) == prefix + tx_hash:
                return string
    raise argparse.ArgumentTypeError(f"Invalid txHash: '{string}'")
