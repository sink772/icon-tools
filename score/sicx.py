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

from icx.icx import ICX
from score import Score
from score.token import IRC2Token
from util import die, in_icx, print_response


class StakedICXManager(Score):
    STAKING_MAN = 'cx43e2eec79eb76293c298f2b17aec06097be606e0'

    def __init__(self, tx_handler):
        super().__init__(tx_handler, self.STAKING_MAN)

    def stake_icx(self, wallet, to, value):
        return self.invoke(wallet, 'stakeICX', {'_to': to}, value=value)

    def claim_unstaked_icx(self, wallet):
        return self.invoke(wallet, 'claimUnstakedICX')

    def claimable_icx(self, address):
        return self.call('claimableICX', {'_address': address})

    def user_unstake_info(self, address):
        return self.call('getUserUnstakeInfo', {'_address': address})

    def ask_to_stake(self, address, keystore):
        maximum = ICX(self._tx_handler).balance(address, False)
        amount = maximum
        value = input('\n==> Amount of transfer in loop: ')
        try:
            amount = int(value)
        except ValueError:
            die(f'Error: value should be integer')
        self.ensure_amount(amount, maximum)
        if self.ask_to_confirm(self.STAKING_MAN, maximum, amount):
            wallet = keystore.get_wallet()
            tx_hash = self.stake_icx(wallet, wallet.get_address(), amount)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def ask_to_claim(self, address, keystore):
        value = self.print_claimable_icx(address)
        if value > 0:
            wallet = keystore.get_wallet()
            tx_hash = self.claim_unstaked_icx(wallet)
            self._tx_handler.ensure_tx_result(tx_hash, True)
        else:
            print("No claimable ICX")

    def print_claimable_icx(self, address):
        hex_value = self.claimable_icx(address)
        price_in_loop = int(hex_value, 16)
        price_in_icx = in_icx(price_in_loop)
        print(f'\n[Claimable ICX]')
        print(f'"{hex_value}" ({price_in_icx:.2f} ICX)')
        return price_in_loop

    @staticmethod
    def ensure_amount(amount, maximum):
        if 0 < amount <= maximum:
            return amount
        die(f'Error: value should be 0 < (value) <= {maximum}')

    @staticmethod
    def ask_to_confirm(address, balance, amount):
        details = {
            "recipient": address,
            "amount": f"{amount} ({in_icx(amount)})",
            "estimated balance after stake": f"{in_icx(balance - amount)} ICX"
        }
        print()
        print_response('Details', details)
        confirm = input('\n==> Are you sure you want to stake? (y/n) ')
        if confirm == 'y':
            return True
        return False

    def get_unstake_info(self, address):
        info = self.user_unstake_info(address)
        if len(info) > 0:
            print()
            print_response('Unstake Info', info)
        else:
            print("No unstake info")


class StakedICX(IRC2Token):

    def __init__(self, tx_handler):
        super().__init__(tx_handler, 'sicx')

    def ask_to_unstake(self, address, keystore):
        _, maximum = self.balance(address)
        amount = maximum
        value = input('\n==> Amount of unstake in loop (or [a]ll): ')
        try:
            if len(value) == 1 and value == 'a':
                pass
            else:
                amount = int(value)
        except ValueError:
            die(f'Error: value should be integer')
        self.ensure_amount(amount, maximum)
        to = StakedICXManager.STAKING_MAN
        if self.ask_to_confirm(to, maximum, amount):
            wallet = keystore.get_wallet()
            data = b'{"method":"unstake"}'
            tx_hash = self.transfer(wallet, to, amount, data)
            self._tx_handler.ensure_tx_result(tx_hash, True)


def add_parser(cmd, subparsers):
    sicx_parser = subparsers.add_parser('sicx', help='[SCORE] Staked ICX')
    sicx_parser.add_argument('--stake', action='store_true', help='stake the given ICX')
    sicx_parser.add_argument('--unstake', action='store_true', help='unstake the given sICX')
    sicx_parser.add_argument('--claim', action='store_true', help='claim unstaked ICX')
    sicx_parser.add_argument('--info', action='store_true', help='get unstake info')

    # register method
    setattr(cmd, 'sicx', run)


def run(args):
    sicx = StakedICX(args.txhandler)
    address = args.keystore.address
    sicx.print_balance(address)
    if args.stake:
        StakedICXManager(args.txhandler).ask_to_stake(address, args.keystore)
    elif args.claim:
        StakedICXManager(args.txhandler).ask_to_claim(address, args.keystore)
    elif args.info:
        StakedICXManager(args.txhandler).get_unstake_info(address)
    elif args.unstake:
        sicx.ask_to_unstake(address, args.keystore)
