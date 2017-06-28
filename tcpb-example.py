#
# Simple example of how to use python and protobuf to interface with a terachem instance, not for general use, too brittle.
#

from tcpb import TCProtobufClient
from protobuf.terachem_server_pb2 import JobInput, Mol  # For JobType and UnitType enumerations

# Water system
atoms = ['O', 'H', 'H']
geom = [0.00000,  0.00000, -0.06852,
        0.00000, -0.79069,  0.54370,
        0.00000,  0.79069,  0.54370]
# Default geom is Bohr (1), but this in Angstrom (0)

# Set up client for h2o job
# Most parameters can be passed into constructor, but you can also use update_options to reset options later
TC = TCProtobufClient(host='localhost', port=54321, method='pbe0', basis='6-31g')
TC.update_options(atoms=atoms, charge=0, spinmult=1, closed=True, restricted=True)

print TC.tc_options

TC.connect()

# Check if the server is available
avail = TC.is_available()
print "TCPB Server available: {}".format(avail)

# Energy calculation
energy = TC.compute_energy(geom, Mol.ANGSTROM)  # Default is BOHR
print "H2O Energy: {}".format(energy)

# Gradient calculation
energy, gradient = TC.compute_gradient(geom, Mol.ANGSTROM)
print "H2O Gradient:\n{}".format(gradient)

# Forces calculation (just like gradient call with -1*gradient)
energy, forces = TC.compute_forces(geom, Mol.ANGSTROM)
print "H2O Forces:\n{}".format(forces)

# General calculation
options = {
    # TeraChem options as key-value pairs
    'maxit':    100,
    'purify':   'no',

    # Some additional keywords are handled by the client
    'bond_order': True,
}
results = TC.compute_job_sync(JobInput.GRADIENT, geom, Mol.ANGSTROM, **options)
print("H2O Results:\n{}".format(results))

# Can get information from last calculation
print("Last H2O Energy: {}".format(TC.prev_results['energy']))

TC.disconnect()
