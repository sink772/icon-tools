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

from iiss.stake import Stake
from util import die, in_icx, get_icon_service, get_address_from_keystore


def balance(args):
    icon_service = get_icon_service(args.endpoint)
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    elif args.address:
        address = args.address
    else:
        die('Error: keystore or address should be specified')
    _balance = icon_service.get_balance(address)
    print('ICX (avail) =', in_icx(_balance))
    if args.all:
        result = Stake(icon_service).query(address)
        current_stake = int(result['stake'], 16)
        print('ICX (stake) =', in_icx(current_stake))
        print('Total ICX =', in_icx(_balance + current_stake))
