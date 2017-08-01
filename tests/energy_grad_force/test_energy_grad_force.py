# Test for simple energy, gradient, and force calculation

import numpy as np
import os
import signal
import subprocess
import sys
import time

from tcpb import TCProtobufClient

sys.path.append('..')
from mock_server import MockServer


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
    'closed': True,
    'restricted': True,
    }

# JOB OUTPUT
tol = 1e-5
h2o_energy = -76.300505
h2o_gradient = [[  0.0000002903,    0.0000000722,   -0.033101313],
                [ -0.0000000608,   -0.0141756697,    0.016550727],
                [ -0.0000002294,    0.0141755976,    0.016550585]]

# RUN TEST
# If run_real_server is True, we expect a real TCPB server and record a packet trace
# For testing purposes, run_real_server should be False and a MockServer + packet trace will be used
run_real_server = False
port = 56789

# Set up MockServer for testing
if not run_real_server:
    mock = MockServer(port, 'client_recv.bin', 'client_sent.bin')

with TCProtobufClient(host='localhost', port=port, trace=run_real_server, **h2o_system) as TC:
    # Energy calculation
    energy = TC.compute_energy(h2o_system['geom'])
    if not np.allclose([h2o_energy], [energy], atol=tol):
        print('Failed energy test')

    # Gradient calculation
    energy, gradient = TC.compute_gradient(h2o_system['geom'])
    if not np.allclose([h2o_energy], [energy], atol=tol) or not np.allclose(h2o_gradient, gradient, atol=tol):
        print('Failed gradient test')

    # Force calculation
    energy, force = TC.compute_forces(h2o_system['geom'])
    if not np.allclose([h2o_energy], [energy], atol=tol) or not np.allclose(h2o_gradient, -force, atol=tol):
        print('Failed force test')

print('Passed energy, gradient, and force tests')
