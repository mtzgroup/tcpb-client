# tests.py
# Written by Stefan Seritan on August 1st, 2017
#
# Unit testing for TCPB clients

import unittest

from available_test import run_test as avail_test
from energy_grad_force_test import run_test as egf_test

class TestTCPB(unittest.TestCase):
    def test_available(self):
        self.assertTrue(avail_test())

    def test_energy_grad_force(self):
       self.assertTrue(egf_test())

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTCPB)
    unittest.TextTestRunner(verbosity=2).run(suite)
