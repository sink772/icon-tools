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

from score.chain import ChainScore
from util import print_response, get_icon_service
from util.txhandler import TxHandler


class Info(object):

    def __init__(self, tx_handler):
        self._tx_handler: TxHandler = tx_handler
        self._chain = ChainScore(tx_handler)

    def get_iiss_info(self):
        return self._chain.call("getIISSInfo")

    def get_network_info(self):
        return self._chain.call("getNetworkInfo")

    def print_next_term(self):
        result = self.get_iiss_info()
        current_block = int(result['blockHeight'], 16)
        next_term = int(result['nextPRepTerm'], 16)
        remaining_block = next_term - current_block
        remaining_seconds = remaining_block * 2
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = (remaining_seconds % 3600) % 60
        time_left = {
            'Blocks': remaining_block,
            'Countdown': f'{hours}:{minutes:02d}:{seconds:02d}'
        }
        print_response('Remaining Time', time_left)

    def print_info(self):
        print_response('IISS Info', self.get_iiss_info())
        print_response('Network Info', self.get_network_info())


def add_parser(cmd, subparsers):
    info_parser = subparsers.add_parser('info', help='Query IISS Information')
    info_parser.add_argument('--next-term', action='store_true', help='show the remaining time to next term')

    # register method
    setattr(cmd, 'info', run)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    info = Info(tx_handler)
    if args.next_term:
        info.print_next_term()
    else:
        info.print_info()
