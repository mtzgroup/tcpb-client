#! /usr/bin/env python
# Test of ci_vec_overlap job through TCPB

from os import path

from tcpb.tcpb import TCProtobufClient as TCPBClient

# Ethylene system
atoms = ['C', 'C', 'H', 'H', 'H', 'H']
geom = [ 0.35673483, -0.05087227, -0.47786734,
         1.61445821, -0.06684947, -0.02916681,
        -0.14997206,  0.87780529, -0.62680155,
        -0.16786485, -0.95561368, -0.69426370,
         2.15270896,  0.84221076,  0.19314809,
         2.16553127, -0.97886933,  0.15232587]
geom2 = [ 0.35673483, -0.05087227, -0.47786734,
          1.61445821, -0.06684947, -0.02916681,
         -0.14997206,  0.87780529, -0.62680155,
         -0.16786485, -0.95561368, -0.69426370,
          2.15270896,  0.84221076,  0.19314809,
          2.16553127, -0.97886933,  0.15232587]


with TCPBClient('localhost', 54321, method='hf', basis='6-31g**') as TC:
    base_options = {
        "atoms":        atoms,
        "charge":       0,
        "spinmult":     1,
        "closed_shell": True,
        "restricted":   True,

        "precision":    "double",
        "threall":      1.0e-20,

        "casci":        "yes",
        "closed":       5,
        "active":       6,
        "cassinglets":  10
    }
    TC.update_options(**base_options)

    # First run CASCI to get some test CI vectors
    options = {
        "directci":     "yes",
        "caswritevecs": "yes"
    }
    results = TC.compute_job_sync("energy", geom, "angstrom", **options)

    # Run ci_vec_overlap job based on last job
    options = {
        "geom2":        geom2,
        "cvec1file":    path.join(results['job_scr_dir'], "CIvecs.Singlet.dat"),
        "cvec2file":    path.join(results['job_scr_dir'], "CIvecs.Singlet.dat"),
        "orb1afile":    path.join(results['job_scr_dir'], "c0"),
        "orb2afile":    path.join(results['job_scr_dir'], "c0")
    }
    results = TC.compute_job_sync("ci_vec_overlap", geom, "angstrom", **options)

    print("Overlap:\n{}".format(results['ci_overlap']))
