import os
from tempfile import TemporaryDirectory

import pystac

from stactools.nrcan_spot_ortho.commands import create_spot_command
from stactools.testing import CliTestCase
from tests.test_utils import write_test_index


class ConvertIndexTest(CliTestCase):
    def create_subcommand_functions(self):
        return [create_spot_command]

    def test_convert_index(self):

        with TemporaryDirectory() as tmp_dir:
            test_index_path = os.path.join(tmp_dir, 'spot_index_test.shp')
            write_test_index(test_index_path)

            cwd = os.getcwd()
            os.chdir(tmp_dir)
            cmd = [
                'nrca-spot-ortho',
                'convert-index',
                test_index_path,
                '.',
                '-t',
            ]
            self.run_command(cmd)
            jsons = [
                os.path.join(dp, f) for dp, dn, filenames in os.walk(tmp_dir)
                for f in filenames if os.path.splitext(f)[1] == '.json'
            ]
            os.chdir(cwd)

            self.assertEqual(len(jsons), 6)

            for json in jsons:
                item_path = os.path.join(tmp_dir, json)
                item = pystac.read_file(item_path)
                item.validate()
