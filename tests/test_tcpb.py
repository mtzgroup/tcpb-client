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

class TestCppTCPB(unittest.TestCase):
    def test_available(self):
        self.assertTrue(available_test.run_cpp_test())

    def test_energy_grad_force(self):
       self.assertTrue(energy_grad_force_test.run_cpp_test())

if __name__ == '__main__':
    py_suite = unittest.TestLoader().loadTestsFromTestCase(TestPyTCPB)
    py_results = unittest.TextTestRunner(verbosity=2).run(py_suite)

    cpp_suite = unittest.TestLoader().loadTestsFromTestCase(TestCppTCPB)
    cpp_results = unittest.TextTestRunner(verbosity=2).run(cpp_suite)

    if len(py_results.errors) or len(py_results.failures):
        print("\n!!! Errors in Python client !!!")
        sys.exit(1)

    if len(cpp_results.errors) or len(cpp_results.failures):
        print("\n!!! Errors in C++ client !!!")
        sys.exit(1)
