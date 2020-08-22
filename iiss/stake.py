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
import time

from iiss.delegate import Delegate
from iiss.iscore import IScore
from score.chain import ChainScore
from util import die, in_icx, in_loop, print_response, get_icon_service, get_address_from_keystore, load_keystore


class Stake(object):

    def __init__(self, service):
        self._chain = ChainScore(service)
        self._icon_service = service
        self._delegate = Delegate(service)

    def balance(self, address):
        return self._icon_service.get_balance(address)

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

    def _check_and_set(self, wallet, address, current_stake, auto_staking):
        balance = self.balance(address)
        status = {
            'staked': in_icx(current_stake),
            'unstaked': in_icx(balance),
        }
        total_icx = in_icx(current_stake + balance)
        print_response('Balance (in ICX)', status)
        print('Total ICX balance =', total_icx)
        if auto_staking:
            new_amount = int(total_icx - 1.0)  # leave 1.0 ICX for future transactions
        else:
            input_value = input('\n==> New staking amount (in ICX)? ')
            new_amount = self._check_value(input_value, int(total_icx))
        self._check_total_delegated(address, in_loop(new_amount))
        print('Requested amount =', new_amount, f'({in_loop(new_amount)} loop)')
        tx_hash = self.set(wallet, new_amount)
        self._ensure_tx_result(tx_hash, auto_staking)

    def ask_to_set(self, address, current_stake, keystore):
        confirm = input('\n==> Are you sure you want to set new staking amount? (y/n) ')
        if confirm == 'y':
            wallet = load_keystore(keystore)
            self._check_and_set(wallet, address, current_stake, False)

    @staticmethod
    def print_status(address, result):
        print('[Stake]')
        print_response(address, result)
        print('StakedICX =', int(result['stake'], 16) / 10**18)

    @staticmethod
    def _check_value(value: str, maximum: int):
        try:
            amount = int(value)
            if 0 <= amount <= maximum:
                return amount
            die(f'Error: value should be 0 <= (value) <= {maximum}')
        except ValueError:
            die(f'Error: value should be integer')

    def _check_total_delegated(self, address, amount):
        total_delegated = self._delegate.get_total_delegated(address)
        if amount <= total_delegated:
            die(f'Error: amount ({amount}) should be larger than the current total delegated ({total_delegated})')

    def _ensure_tx_result(self, tx_hash, wait_result):
        print(f'\n==> https://tracker.icon.foundation/transaction/{tx_hash}')
        count = 0
        while wait_result:
            result = self._icon_service.get_transaction_result(tx_hash, True)
            if 'error' in result:
                print(f'Retry: {result["error"]}')
                count += 1
                if count > 5:
                    die('Error: failed to get transaction result')
                time.sleep(2)
            else:
                print(f'Result: {json.dumps(result, indent=4)}')
                break


class AutoStake(Stake):

    def __init__(self, service):
        super().__init__(service)

    def _claim_iscore(self, wallet, address):
        print('\n>>> Claim IScore:')
        iscore = IScore(self._icon_service)
        result = iscore.query(address)
        iscore.print_status(address, result)
        estimated_icx = in_icx(int(result['estimatedICX'], 16))
        if (estimated_icx - 1.0) <= 0:
            die('Error: EstimatedICX should be larger than 1.0')
        tx_hash = iscore.claim(wallet)
        self._ensure_tx_result(tx_hash, True)

    def _set_stake(self, wallet, address, current_stake):
        print('\n>>> Set staking:')
        self._check_and_set(wallet, address, current_stake, True)

    def _set_delegations(self, wallet, address):
        print('\n>>> Set delegations:')
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
        else:
            die('Error: no delegation or no voting power available')
        tx_hash = self._delegate.set(wallet, delegations)
        self._ensure_tx_result(tx_hash, True)

    def run(self, address, current_stake, keystore):
        wallet = load_keystore(keystore)
        self._claim_iscore(wallet, address)
        self._set_stake(wallet, address, current_stake)
        self._set_delegations(wallet, address)


def run(args):
    icon_service = get_icon_service(args.endpoint)
    stake = Stake(icon_service)
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
            AutoStake(icon_service).run(address, current_stake, args.keystore)
        else:
            stake.ask_to_set(address, current_stake, args.keystore)
    elif args.auto:
        die('Error: "auto" option should be specified with "set"')
