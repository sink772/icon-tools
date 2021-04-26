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

from time import sleep

from iiss.delegate import Delegate
from iiss.iscore import IScore
from score.chain import ChainScore
from util import die, in_icx, in_loop, print_response, get_icon_service, get_address_from_keystore, load_keystore
from util.txhandler import TxHandler


class Stake(object):

    def __init__(self, tx_handler):
        self._tx_handler = tx_handler
        self._chain = ChainScore(tx_handler)
        self._delegate = Delegate(tx_handler)

    def query(self, address):
        params = {
            "address": address
        }
        return self._chain.call("getStake", params)

    def set(self, wallet, amount):
        params = {
            "value": in_loop(amount)
        }
        return self._chain.invoke(wallet, "setStake", params)

    def _get_input(self, total_icx):
        while True:
            try:
                input_value = input('\n==> New staking amount (in ICX)? ')
                return self._check_value(input_value, int(total_icx))
            except KeyboardInterrupt:
                die('exit')
            except ValueError as e:
                print('Error:', e.__str__())
                continue

    def _get_new_amount(self, address, current_stake, auto_staking):
        balance = self._tx_handler.get_balance(address)
        status = {
            'staked': in_icx(current_stake),
            'unstaked': in_icx(balance),
        }
        print()
        print_response('Balance (in ICX)', status)
        total_icx = in_icx(current_stake + balance)
        print('Total ICX balance =', total_icx)
        if auto_staking:
            new_amount = int(total_icx - 1.0)  # leave 1.0 ICX for future transactions
        else:
            new_amount = self._get_input(total_icx)
        self._check_total_delegated(address, in_loop(new_amount))
        print('Requested amount =', new_amount, f'({in_loop(new_amount)} loop)')
        return new_amount

    def ask_to_set(self, address, current_stake, keystore, passwd):
        confirm = input('\n==> Are you sure you want to set new staking amount? (y/n) ')
        if confirm == 'y':
            new_amount = self._get_new_amount(address, current_stake, False)
            wallet = load_keystore(keystore, passwd)
            tx_hash = self.set(wallet, new_amount)
            self._tx_handler.ensure_tx_result(tx_hash, True)

    @staticmethod
    def print_status(address, result):
        print('\n[Stake]')
        print_response(address, result)
        print('StakedICX =', in_icx(int(result['stake'], 16)))

    @staticmethod
    def _check_value(value: str, maximum: int):
        amount = int(value)
        if 0 <= amount <= maximum:
            return amount
        raise ValueError(f'value should be 0 <= (value) <= {maximum}')

    def _check_total_delegated(self, address, amount):
        total_delegated = self._delegate.get_total_delegated(address)
        if amount < total_delegated:
            die(f'Error: amount ({amount}) should be larger than the current total delegated ({total_delegated})')


class AutoStake(Stake):

    def __init__(self, tx_handler):
        super().__init__(tx_handler)
        self._iscore = IScore(tx_handler)

    def _show_status(self, address, current_stake):
        result = self._iscore.query(address)
        self._iscore.print_status(address, result)
        estimated_icx = int(result['estimatedICX'], 16)
        if (in_icx(estimated_icx) - 1.0) <= 0:
            die('Error: EstimatedICX should be larger than 1.0')
        balance = self._tx_handler.get_balance(address)
        total_icx = in_icx(current_stake + balance + estimated_icx)
        new_amount = int(total_icx - 1.0)  # leave 1.0 ICX for future transactions
        print('\nCurrent balance =', in_icx(balance))
        print('Estimated stake amount after auto-staking =', float(new_amount))

    def _claim_iscore(self, wallet):
        print('\n>>> Claim IScore:')
        tx_hash = self._iscore.claim(wallet)
        self._tx_handler.ensure_tx_result(tx_hash, True)

    def _set_stake(self, wallet, address, current_stake):
        print('\n>>> Set staking:')
        new_amount = self._get_new_amount(address, current_stake, True)
        tx_hash = self.set(wallet, new_amount)
        self._tx_handler.ensure_tx_result(tx_hash, True)

    def _set_delegations(self, wallet, address):
        print('\n>>> Set delegations:')
        retry_count = 3
        while True:
            result = self._delegate.query(address)
            delegations = self._delegate.convert_to_map(result['delegations'])
            voting_power = int(result['votingPower'], 16)
            self._delegate.print_delegations(delegations, voting_power, header='Current delegations')
            if len(delegations) > 0 and voting_power > 0:
                # add the remaining voting power to the first
                first = next(iter(delegations))
                amount = voting_power + int(delegations.get(first), 16)
                delegations[first] = hex(amount)
                self._delegate.print_delegations(delegations, 0, header='New delegations')
                tx_hash = self._delegate.set(wallet, delegations)
                self._tx_handler.ensure_tx_result(tx_hash, True)
                return
            else:
                print('Warning: no delegation or no voting power available')
                retry_count -= 1
                if retry_count > 0:
                    print('Retry after 3 seconds...')
                    sleep(3)
                else:
                    die('Exit')

    @staticmethod
    def _ask_to_continue(keystore, passwd):
        if passwd is None:
            confirm = input('\n==> Are you sure you want to continue? (y/n) ')
            if confirm != 'y':
                die('Exit')
        return load_keystore(keystore, passwd)

    def run(self, address, current_stake, keystore, passwd):
        self._show_status(address, current_stake)
        wallet = self._ask_to_continue(keystore, passwd)
        self._claim_iscore(wallet)
        self._set_stake(wallet, address, current_stake)
        self._set_delegations(wallet, address)


def run(args):
    tx_handler = TxHandler(*get_icon_service(args.endpoint))
    stake = Stake(tx_handler)
    if args.keystore:
        address = get_address_from_keystore(args.keystore)
    elif args.address:
        address = args.address
    else:
        die('Error: keystore or address should be specified')
    result = stake.query(address)
    current_stake = int(result['stake'], 16)
    stake.print_status(address, result)
    if args.set:
        if not args.keystore:
            die('Error: keystore should be specified to set staking')
        if args.auto:
            AutoStake(tx_handler).run(address, current_stake, args.keystore, args.password)
        else:
            stake.ask_to_set(address, current_stake, args.keystore, args.password)
    elif args.auto:
        die('Error: "auto" option should be specified with "set"')
