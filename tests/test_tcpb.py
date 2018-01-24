# tests.py
# Written by Stefan Seritan on August 1st, 2017
#
# Unit testing for TCPB clients

import sys
import unittest

import available_test
import energy_grad_force_test

class TestPyTCPB(unittest.TestCase):
    def test_available(self):
        self.assertTrue(available_test.run_py_test())

    def test_energy_grad_force(self):
       self.assertTrue(energy_grad_force_test.run_py_test())

if __name__ == '__main__':
    py_suite = unittest.TestLoader().loadTestsFromTestCase(TestPyTCPB)
    py_results = unittest.TextTestRunner(verbosity=2).run(py_suite)

    failures = False
    if len(py_results.errors) or len(py_results.failures):
        print("\n!!! Errors in Python client !!!")
        failures = True

    if failures is True:
        sys.exit(1)
