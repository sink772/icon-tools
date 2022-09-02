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
from util import get_icon_service, get_address_from_keystore, die, print_response, load_keystore, in_icx
from util.checks import address_type
from util.txhandler import TxHandler


class CraftStaking(Score):
    CFT_STAKING = 'cx2d86ce51600803e187ce769129d1f6442bcefb5b'

    def __init__(self, tx_handler: TxHandler):
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

    def stake(self, address, token, args):
        self.print_balance(address)
        token.ask_to_transfer(args, self._address)

    def unstake(self, wallet, value):
        return self.invoke(wallet, 'unstake', {"_id": 0x0, "_value": value})

    def ask_to_unstake(self, address, args):
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
            wallet = load_keystore(args.keystore, args.password)
            tx_hash = self.unstake(wallet, amount)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    @staticmethod
    def ensure_amount(amount, maximum):
        if 0 < amount <= maximum:
            return amount
        die(f'Error: value should be 0 < (value) <= {maximum}')

    def run(self, args, token):
        if not args.keystore:
            die('Error: keystore should be specified')
        address = get_address_from_keystore(args.keystore)
        if args.stake:
            self.stake(address, token, args)
        elif args.unstake:
            self.ask_to_unstake(address, args)


class CraftReward(Score):
    REWARD_ADDRESS = "cx7ecb16e4c143b95e01d05933c17cb986cfe618e6"

    def __init__(self, tx_handler: TxHandler):
        super().__init__(tx_handler, self.REWARD_ADDRESS)

    def query_rewards(self, address):
        return self.call("queryRewards", {"_address": address})

    def query_lp_rewards(self, address):
        return self.call("queryLpRewards", {"_address": address})

    def query_staking_rewards(self, address):
        return self.call("queryStakingRewards", {"_address": address})

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
            'cft_staking': self.to_int(cft_staking, 'ICX')
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

    def ask_to_claim(self, args):
        confirm = input('\n==> Are you sure you want to claim? (y/n) ')
        if confirm == 'y':
            wallet = load_keystore(args.keystore, args.password)
            if args.claim_lp:
                tx_hash = self.claim_lp_rewards(wallet, args.stake is True)
            elif args.claim_staking:
                tx_hash = self.claim_staking_rewards(wallet, args.stake is True)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    def run(self, args, token):
        if not args.keystore:
            die('Error: keystore should be specified to claim')
        address = get_address_from_keystore(args.keystore)
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
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    address = args.address
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    if not address:
        die('Error: keystore or address should be specified')
    token = IRC2Token(tx_handler, 'cft')
    if args.claim_lp or args.claim_staking:
        CraftReward(tx_handler).run(args, token)
    elif args.stake or args.unstake:
        CraftStaking(tx_handler).run(args, token)
    else:
        token.print_balance(address)
