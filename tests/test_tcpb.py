# tests.py
# Written by Stefan Seritan on August 1st, 2017
#
# Unit testing for TCPB clients

import unittest

import available_test
import energy_grad_force_test

class TestPyTCPB(unittest.TestCase):
    def test_available(self):
        self.assertTrue(available_test.run_py_test())

    def test_energy_grad_force(self):
       self.assertTrue(energy_grad_force_test.run_test())

class TestCppTCPB(unittest.TestCase):
    def test_available(self):
        self.assertTrue(available_test.run_cpp_test())

if __name__ == '__main__':
    py_suite = unittest.TestLoader().loadTestsFromTestCase(TestPyTCPB)
    unittest.TextTestRunner(verbosity=2).run(py_suite)

    #cpp_suite = unittest.TestLoader().loadTestsFromTestCase(TestCppTCPB)
    #unittest.TextTestRunner(verbosity=2).run(cpp_suite)
