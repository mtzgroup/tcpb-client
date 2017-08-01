# tests.py
# Written by Stefan Seritan on August 1st, 2017
#
# Unit testing for TCPB clients

import unittest

from energy_grad_force_test import run_test as egf_test

class TestTCPB(unittest.TestCase):
    def test_energy_grad_force(self):
       self.assertTrue(egf_test())

if __name__ == '__main__':
    unittest.main()
