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

from score import Score
from score.token import IRC2Token
from util import die, print_response, in_icx
from util.checks import address_type


class CraftStaking(Score):
    CFT_STAKING = 'cx2d86ce51600803e187ce769129d1f6442bcefb5b'

    def __init__(self, tx_handler):
        super().__init__(tx_handler, self.CFT_STAKING)

    def balance(self, address, _id):
        return self.call("balanceOf", {"_owner": address, "_id": _id})

    def print_balance(self, address):
        bal = self.balance(address, 0x0)
        price_in_loop = int(bal, 16)
        price_in_icx = in_icx(price_in_loop)
        print(f'\n[Staked]')
        print(f'"{bal}" ({price_in_icx:.2f} CFT)')
        return price_in_loop

    def stake(self, address, token, keystore):
        self.print_balance(address)
        token.ask_to_transfer(keystore, self._address)

    def unstake(self, wallet, value):
        return self.invoke(wallet, 'unstake', {"_id": 0x0, "_value": value})

    def ask_to_unstake(self, address, keystore):
        maximum = self.print_balance(address)
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
        print(f'amount: {amount} ({in_icx(amount)})')
        confirm = input('\n==> Are you sure you want to unstake? (y/n) ')
        if confirm == 'y':
            wallet = keystore.get_wallet()
            tx_hash = self.unstake(wallet, amount)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    @staticmethod
    def ensure_amount(amount, maximum):
        if 0 < amount <= maximum:
            return amount
        die(f'Error: value should be 0 < (value) <= {maximum}')

    def run(self, args, token):
        address = args.keystore.address
        if args.stake:
            self.stake(address, token, args.keystore)
        elif args.unstake:
            self.ask_to_unstake(address, args.keystore)


class CraftReward(Score):
    REWARD_ADDRESS = "cx7ecb16e4c143b95e01d05933c17cb986cfe618e6"

    def __init__(self, tx_handler):
        super().__init__(tx_handler, self.REWARD_ADDRESS)

    def query_rewards(self, address):
        return self.call("queryRewards", {"_address": address})

    def query_lp_rewards(self, address):
        return self.call("queryLpRewards", {"_address": address})

    def query_staking_rewards(self, address):
        return self.call("queryStakingRewards", {"_address": address})

    def current_day(self):
        return self.call("currentDay")

    def last_claimed_day(self, address):
        return self.call("lastClaimedDay", {"_address": address})

    def last_converted_day(self):
        return self.call("lastConvertedDay")

    def claim_lp_rewards(self, wallet, restake: bool):
        param = None
        if restake:
            param = {'_isRestake': "0x1"}
        return self.invoke(wallet, 'claimRewards', param)

    def claim_staking_rewards(self, wallet, compound: bool):
        param = None
        if compound:
            param = {'_isCompound': "0x1"}
        return self.invoke(wallet, 'claimStakingRewards', param)

    def query_all_rewards(self, address):
        liquidity = self.query_rewards(address)
        lp_staking = self.query_lp_rewards(address)
        cft_staking = self.query_staking_rewards(address)
        return {
            'liquidity': self.to_int(liquidity, 'CFT'),
            'lp_staking': self.to_int(lp_staking, 'CFT'),
            'cft_staking': self.to_int(cft_staking, 'bnUSD')
        }

    @staticmethod
    def to_int(hex_str, symbol):
        value = int(hex_str, 16)
        if value == 0:
            return "0"
        return f'{value} ({in_icx(value):.4f} {symbol})'

    def print_rewards(self, address):
        print()
        print_response('[Rewards]', self.query_all_rewards(address))
        last_claimed_day = int(self.last_claimed_day(address), 16)
        current_day = int(self.current_day(), 16)
        print('lastClaimedDay:', last_claimed_day)
        print('lastConvertedDay:', int(self.last_converted_day(), 16))
        print(f'currentDay: {current_day} (delta: {current_day - last_claimed_day})')

    def ask_to_claim(self, args):
        confirm = input('\n==> Are you sure you want to claim? (y/n) ')
        if confirm == 'y':
            wallet = args.keystore.get_wallet()
            if args.claim_lp:
                tx_hash = self.claim_lp_rewards(wallet, args.stake is True)
            elif args.claim_staking:
                tx_hash = self.claim_staking_rewards(wallet, args.stake is True)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def run(self, args, token):
        address = args.keystore.address
        token.print_balance(address)
        self.print_rewards(address)
        self.ask_to_claim(args)


def add_parser(cmd, subparsers):
    cft_parser = subparsers.add_parser('cft', help='[SCORE] CraftNetwork')
    cft_parser.add_argument('--address', type=address_type, help='target address to perform operations')
    cft_parser.add_argument('--claim-lp', action='store_true', help='claim LP rewards')
    cft_parser.add_argument('--claim-staking', action='store_true', help='claim staking rewards')
    cft_parser.add_argument('--stake', action='store_true', help='stake CFT token')
    cft_parser.add_argument('--unstake', action='store_true', help='unstake CFT token')

    # register method
    setattr(cmd, 'cft', run)


def run(args):
    token = IRC2Token(args.txhandler, 'cft')
    if args.claim_lp or args.claim_staking:
        CraftReward(args.txhandler).run(args, token)
    elif args.stake or args.unstake:
        CraftStaking(args.txhandler).run(args, token)
    else:
        address = args.address if args.address else args.keystore.address
        token.print_balance(address)
