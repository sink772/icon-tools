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

import time

from score.chain import ChainScore
from util import print_response, die


class Info(object):

    def __init__(self, tx_handler):
        self._tx_handler = tx_handler
        self._chain = ChainScore(tx_handler)

    def get_iiss_info(self):
        return self._chain.call("getIISSInfo")

    def get_network_info(self):
        return self._chain.call("getNetworkInfo")

    def get_prep_term(self):
        return self._chain.call("getPRepTerm")

    def print_term_info(self, end_block=None):
        term_info = self.get_prep_term()
        period = int(term_info['period'], 16)
        sequence = int(term_info['sequence'], 16)
        start_block = int(term_info['startBlockHeight'], 16)
        current_block = int(term_info['blockHeight'], 16)
        print_response('Current', {
            'Start': f"{start_block}",
            'Now': f"{current_block} (elapsed: {current_block - start_block})",
            'Sequence': sequence,
            'Period': period,
        })
        if not end_block:
            end_block = int(term_info['endBlockHeight'], 16)
        elif end_block <= current_block:
            die(f'Error: end_block must be greater than current_block={current_block}')
        remaining_block = end_block - current_block
        remaining_seconds = remaining_block * 2
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = (remaining_seconds % 3600) % 60
        print_response('Next', {
            'Remaining': f"{remaining_block}",
            'Countdown': f'{hours}:{minutes:02d}:{seconds:02d}',
            'EndAt': time.ctime(time.time() + remaining_seconds)
        })

    def print_info(self):
        print_response('IISS Info', self.get_iiss_info())
        print_response('Network Info', self.get_network_info())


def add_parser(cmd, subparsers):
    info_parser = subparsers.add_parser('info', help='Query IISS Information')
    info_parser.add_argument('--term', action='store_true', help='show the term info')
    info_parser.add_argument('--end-block', type=int, help='show the remaining time to end block')

    # register method
    setattr(cmd, 'info', run)


def run(args):
    info = Info(args.txhandler)
    if args.term:
        info.print_term_info()
    elif args.end_block:
        info.print_term_info(args.end_block)
    else:
        info.print_info()
