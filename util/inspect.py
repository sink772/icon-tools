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

import json
import os
import subprocess
import tempfile
import zipfile

from score.gov import Governance
from util import die


class Inspect(object):

    def __init__(self, tx_handler, keystore, endpoint):
        self._tx_handler = tx_handler
        self._keystore = keystore
        self._endpoint = endpoint

    def download_contract(self, json_file):
        with open(json_file, "r") as f:
            contracts: dict = json.loads(f.read())
        gov = Governance(self._tx_handler)
        tempdir = tempfile.mkdtemp(prefix="download-", dir=".")
        for address in contracts.keys():
            print(address)
            status = gov.get_score_status(address)
            current = status['current']
            owner = status['owner']
            if owner.startswith("hx") and current['deployTxHash'] == current['auditTxHash']:
                tx_hash = current['deployTxHash']
                result = self._tx_handler.get_tx_by_hash(tx_hash)
                if 'result' in result:
                    raw_tx = result['result']
                    content = bytes.fromhex(raw_tx['data']['content'][2:])
                    filename = f"{address}_{tx_hash[2:8]}.jar"
                    with open(os.path.join(tempdir, filename), 'wb') as dest:
                        dest.write(content)
                    print('Downloaded', filename)
                else:
                    die('Error: failed to get transaction data')
            else:
                if owner.startswith("cx"):
                    print("Warn: owner is", owner)
                else:
                    die(f'Error: {status}')

    def run(self, args):
        path = args.rootdir
        outdir = path + "-out"
        print(f'outdir={outdir}')
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        count = 0
        for dirpath, dirnames, filenames in os.walk(path):
            count += 1
            print(f"[{count}] dirpath={dirpath}")
            for file in filenames:
                if file.endswith(".jar"):
                    self.work_with_zipfile(dirpath, file, outdir)

    @staticmethod
    def work_with_zipfile(dirpath, file, outdir):
        code_jar = os.path.join(dirpath, file)
        tempdir = tempfile.mkdtemp(prefix="inspect-", dir=outdir)
        purge_tmpdir = True
        with zipfile.ZipFile(code_jar, 'r') as zf:
            for f in zf.filelist:
                if f.filename.endswith(".class"):
                    zf.extract(f, tempdir)
                    cf = os.path.join(tempdir, f.filename)
                    cmd = ['java', '-jar', '/ws/jdk/asmtools-7.0-build/release/lib/asmtools.jar', 'jdis', cf]
                    ret = subprocess.run(cmd, capture_output=True)
                    # idx = ret.stdout.find(b'Enum.valueOf')
                    idx = ret.stdout.find(b'Method score/Context.call:"(Ljava/lang/Class;')
                    # idx = ret.stdout.find(b'Method java/util/Map.values')
                    # idx = ret.stdout.find(b'getPRepStats')
                    # idx = ret.stdout.find(b'Method java/lang/StringBuilder')
                    if idx > 0:
                        idx2 = ret.stdout.find(b'\n', idx)
                        print(f"\tFound: {code_jar}/{f.filename}")
                        print(f"\t\tat {cf}")
                        print(f"\t\t{ret.stdout[idx:idx2]}")
                        purge_tmpdir = False
                    else:
                        os.remove(cf)
        if purge_tmpdir:
            os.rmdir(tempdir)


def add_parser(cmd, subparsers):
    name = __name__.split(".")[-1]
    inspect_parser = subparsers.add_parser(name, help='Perform inspect operations')
    inspect_parser.add_argument('--rootdir', type=str, help='Root dir for searching jars')
    inspect_parser.add_argument('--download', type=str, metavar='CONTRACTS_JSON', help='Download contracts')

    # register method
    setattr(cmd, name, run)


def run(args):
    inspect = Inspect(args.txhandler, args.keystore, args.endpoint)
    json_file = args.download
    if json_file:
        inspect.download_contract(json_file)
    else:
        inspect.run(args)
