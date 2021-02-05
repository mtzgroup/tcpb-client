# Test for simple energy, gradient, and force calculation

import numpy as np
import os
import signal
import subprocess
import sys
import time

from tcpb import TCProtobufClient

from .mock_server import MockServer


# JOB INPUT
h2o_system = {
    'atoms': ['O', 'H', 'H'],
    'geom': [0.00000,  0.00000, -0.12948,
             0.00000, -1.49419,  1.02744,
             0.00000,  1.49419,  1.02744],
    'method': 'pbe0',
    'basis': '6-31g',
    'charge': 0,
    'spinmult': 1,
    'closed_shell': True,
    'restricted': True,
    }

# JOB OUTPUT
tol = 1e-5
h2o_energy = -76.300505
h2o_gradient = [[  0.0000033590,   -0.0000021343,   -0.0331173999],
                [ -0.0000006941,   -0.0141806788,    0.0165585893],
                [ -0.0000026649,    0.0141828094,    0.0165588269]]

def run_py_test(port=54321, run_real_server=False):
    """Run the test using Python client

    Args:
        port: Port to use for server and client in testing
        run_real_server: If True, we expect a real TCPB server and record a packet trace
                         If False, run the test with MockServer and the recorded packet trace
    Returns True if passed the tests, and False if failed the tests
    """
    # Set up MockServer for testing
    if not run_real_server:
        script_dir = os.path.dirname(__file__)
        recv_file = os.path.join(script_dir, 'energy_grad_force/client_recv.bin')
        sent_file = os.path.join(script_dir, 'energy_grad_force/client_sent.bin')
        mock = MockServer(port, recv_file, sent_file)

    with TCProtobufClient(host='localhost', port=port, trace=run_real_server) as TC:
        if run_real_server:
            print('TCPB Client Protobuf:')
            print(h2o_system)

        # Energy calculation
        energy = TC.compute_energy(**h2o_system)
        if not np.allclose([h2o_energy], [energy], atol=tol):
            print('Failed energy test')
            return False

        # Gradient calculation
        energy, gradient = TC.compute_gradient(**h2o_system)
        if not np.allclose([h2o_energy], [energy], atol=tol) or not np.allclose(h2o_gradient, gradient, atol=tol):
            print('Failed gradient test')
            return False

        # Force calculation
        energy, force = TC.compute_forces(**h2o_system)
        if not np.allclose([h2o_energy], [energy], atol=tol) or not np.allclose(h2o_gradient, -force, atol=tol):
            print('Failed force test')
            return False

    return True

def run_cpp_test(port=56789):
    """Run the test using an external C++ script in energy_grad_force/
    Note that the expected answer is hardcoded in C++
    If you change the test, make sure to update the C++ as well

    Args:
        port: Port to use for server and client in testing
    Returns True if passed the tests, and False if failed the tests
    """
    # Set up MockServer for testing
    mock = MockServer(port, 'energy_grad_force/client_recv.bin', 'energy_grad_force/client_sent.bin')

    # Subprocess out, expect a returncode of 1 for failure and 0 for success
    rc = subprocess.call("./energy_grad_force/energy_grad_force_test localhost {}".format(port), shell=True)

    if rc:
        return False

    return True

if __name__ == '__main__':
    #run_py_test(run_real_server=True)

    print("Running Python test...")
    run_py_test()

    #print("Running C++ test...")
    #run_cpp_test()

