import unittest

import stactools.nrcan_spot_ortho


class TestModule(unittest.TestCase):
    def test_version(self):
        self.assertIsNotNone(stactools.nrcan_spot_ortho.__version__)
