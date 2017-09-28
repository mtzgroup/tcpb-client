#!/usr/bin/env python
# Basic TCProtobufClient usage

from tcpb import TCProtobufClient

# Water system
atoms = ['O', 'H', 'H']
geom = [0.00000,  0.00000, -0.06852,
        0.00000, -0.79069,  0.54370,
        0.00000,  0.79069,  0.54370]
# Default geom is bohr, but this in angstrom

# Set up client for h2o job
# Most parameters can be passed into constructor, but you can also use update_options to reset options later
TC = TCProtobufClient(host='localhost', port=54321)
TC.update_options(atoms=atoms, charge=0, spinmult=1, closed_shell=True, restricted=True, method='pbe0', basis='6-31g')

print TC.tc_options

TC.connect()

# Check if the server is available
avail = TC.is_available()
print "TCPB Server available: {}".format(avail)

# Energy calculation
energy = TC.compute_energy(geom, "angstrom")  # Default is BOHR
print "H2O Energy: {}".format(energy)

# Gradient calculation
energy, gradient = TC.compute_gradient(geom, "angstrom")
print "H2O Gradient:\n{}".format(gradient)

# Forces calculation (just like gradient call with -1*gradient)
energy, forces = TC.compute_forces(geom, "angstrom")
print "H2O Forces:\n{}".format(forces)

# General calculation
options = {
    # TeraChem options as key-value pairs
    'maxit':    100,
    'purify':   'no',

    # Some additional keywords are handled by the client
    'bond_order': True,
}
results = TC.compute_job_sync("gradient", geom, "angstrom", **options)
print("H2O Results:\n{}".format(results))

# Can get information from last calculation
print("Last H2O Energy: {}".format(TC.prev_results['energy']))

TC.disconnect()
