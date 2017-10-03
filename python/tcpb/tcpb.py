"""tcpb.py:
Simple Python socket client for communicating with TeraChem Protocol Buffer servers
"""

import sys
import numpy as np
import socket
import struct
import logging

# Import the Protobuf messages generated from the .proto file
# Note that I have implemented a small protocol on top of the protobufs since we send them in binary over TCP
# ALL MESSAGES ARE REQUIRED TO HAVE AN 8 BYTE HEADER
# First 4 bytes: int32 of protocol buffer message type (check the MessageType enum in the protobuf file)
# Second 4 bytes: int32 of packet size (not including the header)
from . import terachem_server_pb2 as pb


class TCProtobufClient(object):
    """Connect and communicate with a TeraChem instance running in Protocol Buffer server mode
    (i.e. TeraChem was started with the -s|--server flag)
    """
    def __init__(self, host, port, debug=False, trace=False,
                 atoms=None, charge=0, spinmult=1, closed_shell=None, restricted=None,
                 method=None, basis=None, **kwargs):
        """Initialize a TCProtobufClient object.

        Args:
            host: String of hostname
            port: Integer of port number (must be above 1023)
            debug: If True, assumes connections work (used for testing with no server)
            trace: If True, packets are saved to .bin files (which can then be used for testing)
            atoms: List of atoms types as strings
            charge: Total charge (int)
            spinmult: Spin multiplicity (int)
            closed_shell: Whether to run as closed-shell (bool)
            restricted: Whether to run as restricted (bool)
            method: TeraChem method (string)
            basis: TeraChem basis (string)
            **kwargs: Additional TeraChem keywords (dict of key-value pairs as strings)
        """
        self.debug = debug
        self.trace = trace
        if self.trace:
            self.intracefile = open('client_recv.bin', 'wb')
            self.outtracefile = open('client_sent.bin', 'wb')

        # Socket options
        self.update_address(host, port)
        self.tcsock = None
        # Would like to not hard code this, but the truth is I am expecting exactly 8 bytes, not whatever Python thinks 2 ints is
        self.header_size = 8

        # Store options directly in Protobufs
        self.tc_options = pb.JobInput()
        # Since protobuf defaults to not None ([], 0, False, etc.), I have to explicitly check whether things were set by the user
        self.atoms_set = False
        self.charge_set = False
        self.spinmult_set = False
        self.closed_shell_set = False
        self.restricted_set = False
        self.method_set = False
        self.basis_set = False
        self.update_options(atoms, charge, spinmult, closed_shell, restricted, method, basis, **kwargs)

        self.prev_results = None

    def __enter__(self):
        """
        Allow automatic context management using 'with' statement

        >>> with TCProtobufClient(host, port, **options) as TC:
        >>>     E = TC.compute_energy(geom)
        """
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        """
        Disconnect in automatic context management.
        """
        self.disconnect() 

    def setup(self, mol, closed_shell=None, restricted=None):
        """Convenience routine to setup molecular parameters using a molecule object.

        Args:
            mol:    A molecule object similar to core.molecule.Molecule that have fields
                    `atoms`, `charge` and `multiplicity`
        """
        # Check if mol contains all proper fields
        if not set(['atoms', 'charge', 'multiplicity']).issubset(set(dir(mol))):
            raise AttributeError("Invalid argument to setup(). "
                                 "Attributes atoms, charge and multiplicity are required")

        self.update_options(mol.atoms, mol.charge, mol.multiplicity, closed_shell, restricted)

    def update_options(self, atoms=None, charge=None, spinmult=None, closed_shell=None, restricted=None,
                       method=None, basis=None, **kwargs):
        """Update the TeraChem options of a TCProtobufClient object.

        If an argument is passed as None, the value does not change.
        If a molecule option or basis is changed, TeraChem will regenerate MOs on next job.

        Args:
            atoms:          List of atoms types as strings
            charge:         Total charge (int)
            spinmult:       Spin multiplicity (int)
            closed_shell:   Whether to run as closed-shell (bool)
            restricted:     Whether to run as restricted (bool)
            method:         TeraChem method (string)
            basis:          TeraChem basis (string)
            **kwargs:       Additional TeraChem keywords, see _process_kwargs for details
        """
        # Sanity checks
        if atoms is not None:
            # if not isinstance(atoms, list):
            #    raise TypeError("Atoms must be given as a list")
            for atom in atoms:
                # TODO: Convert integers to string by element number
                if not isinstance(atom, basestring):
                    raise TypeError("Atom type must be given as a string")
        if charge is not None and not isinstance(charge, int):
            raise TypeError("Charge must be an integer")
        if spinmult is not None:
            if not isinstance(spinmult, int):
                raise TypeError("Spin multiplicity must be an integer")
            if closed_shell is None and self.tc_options.mol.closed is True and spinmult != 1:
                print("WARNING: Spin multiplicity greater than 1 but molecule set as closed, setting closed_shell to False")
                closed_shell = False
            if closed_shell is True and spinmult != 1:
                print("WARNING: Molecule cannot be closed with a spin multiplicity greater than 1, setting closed_shell to False")
                closed_shell = False
            if restricted is None and self.tc_options.mol.restricted is True and spinmult != 1:
                print("WARNING: Spin multiplicity greater than 1 but molecule set as restricted, setting restricted to False")
                restricted = False
            if restricted is True and spinmult != 1:
                print("WARNING: Cannot specify restricted with a spin multiplicity greater than 1, setting restricted to False")
                restricted = False
        if closed_shell is not None and not isinstance(closed_shell, bool):
            raise TypeError("Closed must be either True or False")
        if restricted is not None and not isinstance(restricted, bool):
            raise TypeError("Closed must be either True or False")
        if closed_shell is True and restricted is False:
            print("WARNING: Cannot have a closed unrestricted system, setting to closed_shell to False")
            closed_shell = False

        if method is not None:
            if not isinstance(method, basestring):
                raise TypeError("TeraChem method must be a string")
            elif method.upper() not in pb.JobInput.MethodType.keys():
                raise ValueError("Method specified is not available in this version of the TCPB client\n" \
                                 "Allowed methods: {}".format(pb.JobInput.MethodType.keys()))
        if basis is not None:
            if not isinstance(basis, basestring):
                raise TypeError("TeraChem basis must be a string")
                # TODO: Check like method

        # Molecule options
        if atoms is not None:
            del self.tc_options.mol.atoms[:]
            self.tc_options.mol.atoms.extend(atoms)
            self.atoms_set = True
        if charge is not None:
            self.tc_options.mol.charge = charge
            self.charge_set = True
        if spinmult is not None:
            self.tc_options.mol.multiplicity = spinmult
            self.spinmult_set = True
        if closed_shell is not None:
            self.tc_options.mol.closed = closed_shell
            self.closed_shell_set = True
        if restricted is not None:
            self.tc_options.mol.restricted = restricted
            self.restricted_set = True

        # TeraChem options
        if method is not None:
            self.tc_options.method = pb.JobInput.MethodType.Value(method.upper())
            self.method_set = True
        if basis is not None:
            self.tc_options.basis = basis
            self.basis_set = True

        if atoms is not None or charge is not None or spinmult is not None or \
           closed_shell is not None or restricted is not None or method is not None or basis is not None:
            self.tc_options.orb1afile = ""
            self.tc_options.orb1bfile = ""

        self._process_kwargs(self.tc_options, **kwargs)

    def update_address(self, host, port):
        """Update the host and port of a TCProtobufClient object.
        Note that you will have to call disconnect() and connect() before and after this
        yourself to actually connect to the new server.

        Args:
            host: String of hostname
            port: Integer of port number (must be above 1023)
        """
        # Sanity checks
        if not isinstance(host, basestring):
            raise TypeError("Hostname must be a string")
        if not isinstance(port, int):
            raise TypeError("Port number must be an integer")
        if port < 1023:
            raise ValueError("Port number is not allowed to below 1023 (system reserved ports)")

        # Socket options
        self.tcaddr = (host, port)

    def connect(self):
        """Connect to the TeraChem Protobuf server
        """
        if self.debug:
            logging.info('in debug mode - assume connection established')
            return

        try:
            self.tcsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcsock.settimeout(60.0)  # Timeout of 1 minute
            self.tcsock.connect(self.tcaddr)
        except socket.error as msg:
            raise RuntimeError("TCProtobufClient: Problem connecting to {}. Error: {}".format(self.tcaddr, msg))

    def disconnect(self):
        """Disconnect from the TeraChem Protobuf server
        """
        if self.debug:
            logging.info('in debug mode - assume disconnection worked')
            return

        try:
            self.tcsock.shutdown(2)  # Shutdown read and write
            self.tcsock.close()
            self.tcsock = None
        except socket.error as msg:
            raise RuntimeError("TCProtobufClient: Problem disconnecting from {}. Error: {}".format(self.tcaddr, msg))

    def is_available(self):
        """Asks the TeraChem Protobuf server whether it is available or busy through the Status protobuf message.
        Note that this does not reserve the server, and the status could change after this function is called.

        Returns true if the TeraChem PB server is currently available (no running job)
        """
        if self.debug:
            logging.info('in debug mode - assume terachem server is available')
            return True

        # Send Status message 
        self._send_msg(pb.STATUS, None)

        # Receive Status header
        status = self._recv_msg(pb.STATUS)

        return not status.busy

    def send_job_async(self, jobType="energy", geom=None, unitType="bohr", **kwargs):
        """Pack and send the current JobInput to the TeraChem Protobuf server asynchronously.
        This function expects a Status message back that either tells us whether the job was accepted.

        Args:
            jobType:    Job type key, as defined in the pb.JobInput.RunType enum (defaults to "energy")
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to "bohr")
            **kwargs:   Additional TeraChem keywords, check _process_kwargs for behaviour

        Returns True on job acceptance, False on server busy, and errors out if communication fails
        """
        # Check if previous molecule setup is available
        if self.atoms_set is False:
            raise LookupError("send_job_async() called before atoms were set.")
        if self.charge_set is False:
            raise LookupError("send_job_async() called before charge was set.")
        if self.spinmult_set is False:
            raise LookupError("send_job_async() called before spin multiplicity was set.")
        if self.closed_shell_set is False:
            raise LookupError("send_job_async() called before closed_shell was set.")
        if self.restricted_set is False:
            raise LookupError("send_job_async() called before restricted was set.")
        if self.method_set is False:
            raise LookupError("send_job_async() called before method was set.")
        if self.basis_set is False:
            raise LookupError("send_job_async() called before basis was set.")

        if jobType.upper() not in pb.JobInput.RunType.keys():
            raise ValueError("Job type specified is not available in this version of the TCPB client\n" \
                             "Allowed run types: {}".format(pb.JobInput.RunType.keys()))
        if geom is None:
            raise SyntaxError("Did not provide geometry to send_job_async()")
        if isinstance(geom, np.ndarray):
            geom = geom.flatten()
        if len(self.tc_options.mol.atoms) != len(geom)/3.0:
            raise ValueError("Geometry does not match atom list in send_job_async()")
        if unitType.upper() not in pb.Mol.UnitType.keys():
            raise ValueError("Unit type specified is not available in this version of the TCPB client\n" \
                             "Allowed unit types: {}".format(pb.Mol.UnitType.keys()))

        if self.debug:
            logging.info("in debug mode - assume job completed")
            return True

        # Job setup
        self.tc_options.run = pb.JobInput.RunType.Value(jobType.upper())
        del self.tc_options.mol.xyz[:]
        self.tc_options.mol.xyz.extend(geom)
        self.tc_options.mol.units = pb.Mol.UnitType.Value(unitType.upper())

        # Handle kwargs for this specific job
        job_options = pb.JobInput()
        job_options.CopyFrom(self.tc_options)
        self._process_kwargs(job_options, **kwargs)

        self._send_msg(pb.JOBINPUT, job_options)

        status = self._recv_msg(pb.STATUS)

        if status.WhichOneof("job_status") == "accepted":
            return True
        else:
            return False

    def check_job_complete(self):
        """Pack and send a Status message to the TeraChem Protobuf server asynchronously.
        This function expects a Status message back with either working or completed set.
        Errors out if just busy message returned, implying the job we are checking was not submitted
        or had some other issue

        Returns True if job is completed, False otherwise
        """

        if self.debug:
            logging.info("in debug mode - assume check_job_complete is True")
            return True

        # Send Status
        self._send_msg(pb.STATUS, None)

        # Receive Status
        status = self._recv_msg(pb.STATUS)

        if status.WhichOneof("job_status") == "completed":
            return True
        elif status.WhichOneof("job_status") == "working":
            return False
        else:
            raise RuntimeError("TCProtobufClient: No valid job status received in check_job_complete(),\
                                either no job submitted or major issue with server.")

    def recv_job_async(self):
        """Recv and unpack a JobOutput message from the TeraChem Protobuf server asynchronously.
        This function expects the job to be ready (i.e. check_job_complete() returned true),
        so will error out on timeout.

        Creates a results dictionary that mirrors the JobOutput message, using NumPy arrays when appropriate.
        Results are also saved in the prev_results class member.
        An inclusive list of the results members (with types):
            atoms:              Flat # of atoms NumPy array of 2-character strings
            geom:               # of atoms by 3 NumPy array of doubles
            energy:             Either empty, single energy, or flat # of cas_energy_labels of NumPy array of doubles
            charges:            Flat # of atoms NumPy array of doubles
            spins:              Flat # of atoms NumPy array of doubles
            dipole_moment:      Single element
            dipole_vector:      Flat 3-element NumPy array of doubles
            job_dir:            String
            job_scr_dir:        String
            server_job_id:      Int
            orbfile:            String (if restricted is True, otherwise not included)
            orbfile_a:          String (if restricted is False, otherwise not included)
            orbfile_b:          String (if restricted is False, otherwise not included)
        Additional (optional) members of results:
            gradient:           # of atoms by 3 NumPy array of doubles (if available)
            cas_energy_labels:  List of tuples of (state, multiplicity) corresponding to the energy list
            bond_order:         # of atoms by # of atoms NumPy array of doubles
            ci_overlap:         ci_overlap_size by ci_overlap_size NumPy array of doubles
        Also sets the orbital files from the JobOutput message into the next JobInput message.

        Returns the results dictionary.
        """
        output = self._recv_msg(pb.JOBOUTPUT)

        # Set MOs for next job
        self.tc_options.orb1afile = output.orb1afile
        self.tc_options.orb1bfile = output.orb1bfile

        # Parse output into normal python dictionary
        results = {
            'atoms'         : np.array(output.mol.atoms, dtype='S2'),
            'geom'          : np.array(output.mol.xyz, dtype=np.float64).reshape(-1, 3),
            'charges'       : np.array(output.charges, dtype=np.float64),
            'spins'         : np.array(output.spins, dtype=np.float64),
            'dipole_moment' : output.dipoles[3],
            'dipole_vector' : np.array(output.dipoles[:3], dtype=np.float64),
            'job_dir'       : output.job_dir,
            'job_scr_dir'   : output.job_scr_dir,
            'server_job_id' : output.server_job_id
        }

        if len(output.energy):
            results['energy'] = output.energy[0]

        if output.mol.restricted is True:
            results['orbfile'] = output.orb1afile
        else:
            results['orbfile_a'] = output.orb1afile
            results['orbfile_b'] = output.orb1bfile

        if len(output.gradient):
            results['gradient'] = np.array(output.gradient, dtype=np.float64).reshape(-1, 3)

        if len(output.nacme):
            results['nacme'] = np.array(output.nacme, dtype=np.float64).reshape(-1, 3)

        if len(output.cas_energy_states):
            results['energy'] = np.array(output.energy[:len(output.cas_energy_states)], dtype=np.float64)
            results['cas_energy_labels'] = zip(output.cas_energy_states, output.cas_energy_mults)

        if len(output.bond_order):
            nAtoms = len(output.mol.atoms)
            results['bond_order'] = np.array(output.bond_order, dtype=np.float64).reshape(nAtoms, nAtoms)

        if len(output.ci_overlaps):
            results['ci_overlap'] = np.array(output.ci_overlaps, dtype=np.float64).reshape(output.ci_overlap_size, output.ci_overlap_size)

        # Save results for user access later
        self.prev_results = results

        return results

    def compute_job_sync(self, jobType="energy", geom=None, unitType="bohr", **kwargs):
        """Wrapper for send_job_async() and recv_job_async(), using check_job_complete() to poll the server.

        Args:
            jobType:    Job type key, as defined in the pb.JobInput.RunType enum (defaults to 'energy')
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check _process_kwargs for behaviour

        Returns a results dictionary that mirrors the JobOutput message, using reshaped NumPy arrays when possible
        """
        if self.debug:
            logging.info("in debug mode - assume compute_job_sync completed successfully")
            return True

        accepted = self.send_job_async(jobType, geom, unitType, **kwargs)
        while accepted is False:
            accepted = self.send_job_async(jobType, geom, unitType, **kwargs)

        completed = self.check_job_complete()
        while completed is False:
            completed = self.check_job_complete()

        return self.recv_job_async()

    # CONVENIENCE FUNCTIONS #
    def compute_energy(self, geom=None, unitType="bohr", **kwargs):
        """Compute energy of a new geometry, but with the same atom labels/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check _process_kwargs for behaviour

        Returns energy
        """
        results = self.compute_job_sync("energy", geom, unitType, **kwargs)
        return results['energy']

    def compute_gradient(self, geom=None, unitType="bohr", **kwargs):
        """Compute gradient of a new geometry, but with the same atom labels/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check _process_kwargs for behaviour

        Returns a tuple of (energy, gradient)
        """
        results = self.compute_job_sync("gradient", geom, unitType, **kwargs)
        return results['energy'], results['gradient']

    # Convenience to maintain compatibility with NanoReactor2
    def compute_forces(self, geom=None, unitType="bohr", **kwargs):
        """Compute forces of a new geometry, but with the same atoms labels/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check _process_kwargs for behaviour

        Returns a tuple of (energy, forces), which is really (energy, -gradient)
        """
        results = self.compute_job_sync("gradient", geom, unitType, **kwargs)
        return results['energy'], -1.0*results['gradient']

    def compute_coupling(self, geom=None, unitType="bohr", **kwargs):
        """Compute nonadiabatic coupling of a new geometry, but with the same atoms labels/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check _process_kwargs for behaviour

        Returns a len(atoms) by 3 NumPy array of doubles of the nonadiabatic coupling vector
        """
        results = self.compute_job_sync("coupling", geom, unitType, **kwargs)
        return results['nacme']


    def compute_ci_overlap(self, geom=None, geom2=None, cvec1file=None, cvec2file=None,
        orb1afile=None, orb1bfile=None, orb2afile=None, orb2bfile=None, unitType="bohr", **kwargs):
        """Compute wavefunction overlap given two different geometries, CI vectors, and orbitals,
        using the same atom labels/charge/spin multiplicity as the previous calculation.
        
        To run a closed shell calculation, only populate orb1afile/orb2afile, leaving orb1bfile/orb2bfile blank.
        Currently, open-shell overlap calculations are not supported by TeraChem.

        Args:
            geom:       Cartesian geometry of the first point
            geom2:      Cartesian geometry of the second point
            cvec1file:  Binary file of CI vector for first geometry (row-major, double64)
            cvec2file:  Binary file of CI vector for second geometry (row-major, double64)
            orb1afile:  Binary file of alpha MO coefficients for first geometry (row-major, double64)
            orb1bfile:  Binary file of beta MO coefficients for first geometry (row-major, double64)
            orb2afile:  Binary file of alpha MO coefficients for second geometry (row-major, double64)
            orb2bfile:  Binary file of beta MO coefficients for second geometry (row-major, double64)
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check _process_kwargs for behaviour

        Returns a NumPy array of state overlaps
        """
        if geom is None or geom2 is None:
            raise SyntaxError("Did not provide two geometries to compute_ci_overlap()")
        if cvec1file is None or cvec2file is None:
            raise SyntaxError("Did not provide two CI vectors to compute_ci_overlap()")
        if orb1afile is None or orb1bfile is None:
            raise SyntaxError("Did not provide two sets of orbitals to compute_ci_overlap()")
        if (orb1bfile is not None and orb2bfile is None) or (orb1bfile is None and orb2bfile is not None) and self.tc_options.mol.closed is False:
            raise SyntaxError("Did not provide two sets of open-shell orbitals to compute_ci_overlap()")
        elif orb1bfile is not None and orb2bfile is not None and self.tc_options.mol.closed is True:
            print("WARNING: System specified as closed, but open-shell orbitals were passed to compute_ci_overlap(). Ignoring beta orbitals.")

        # Wipe MO coefficients
        self.tc_options.orb1afile = ""
        self.tc_options.orb1bfile = ""

        if self.tc_options.mol.closed:
            results = self.compute_job_sync("ci_vec_overlap", geom, unitType, geom2=geom2,
                cvec1file=cvec1file, cvec2file=cvec2file,
                orb1afile=orb1afile, orb2afile=orb2afile, **kwargs)
        else:
            raise RuntimeError("WARNING: Open-shell systems are currently not supported for overlaps")
            #results = self.compute_job_sync("ci_vec_overlap", geom, unitType, geom2=geom2,
            #    cvec1file=cvec1file, cvec2file=cvec2file,
            #    orb1afile=orb1afile, orb1bfile=orb1bfile,
            #    orb2afile=orb1bfile, orb2bfile=orb2bfile, **kwargs)
            
        return results['ci_overlap']

    # Serialization helper functions
    def read_orbfile(self, orbfile, num_rows, num_cols):
        """Deserialize a TeraChem binary orbital file of doubles.

        HF/DFT orbitals (which are stored column-major for TeraChem) are transposed on deserialization.

        Args:
            orbfile: Filename of orbital file to read
            num_rows: Rows in MO coefficient matrix
            num_cols: Columns in MO coefficient matrix
        Returns a (num_rows, num_cols) NumPy array of MO coefficients
        """
        orbs = np.fromfile(orbfile, dtype=np.float64)

        orbs = orbs.reshape((num_rows, num_cols))

        if orbfile.endswith('c0') or orbfile.endswith('ca0') or orbfile.endswith('cb0'):
            orbs = orbs.transpose()

        return orbs

    def write_orbfile(self, orbs, orbfile):
        """Serialize a TeraChem binary orbital file of doubles.

        HF/DFT orbitals (which are stored column-major for TeraChem) are transposed on serialization.

        Args:
            orbs: Non-flat NumPy array of MO coefficients
            orbfile: Filename of orbital file to write 
        """
        if not isinstance(orbs, np.ndarray) or len(orbs.shape) != 2:
            raise SyntaxError("Need a shaped NumPy array for write_orbfile to do proper serialization for TeraChem.")

        if orbfile.endswith('c0') or orbfile.endswith('ca0') or orbfile.endswith('cb0'):
            orbs = orbs.transpose()

        orbs.astype(np.float64).tofile(orbfile)

    def read_ci_vector(self, cvecfile, num_rows, num_cols):
        """Deserialize a TeraChem binary CI vector file of doubles.

        Args:
            cvecfile: Filename of CI vector file to read
            num_rows: Rows in CI vector 
            num_cols: Columns in CI vector matrix
        Returns a (num_rows, num_cols) NumPy array of MO coefficients
        """
        ci_vector = np.fromfile(cvecfile, dtype=np.float64)

        return ci_vector.reshape((num_rows, num_cols))

    def write_ci_vector(self, ci_vector, orbfile):
        """Serialize a TeraChem binary CI vector file of doubles.

        Args:
            ci_vector: Non-flat NumPy array of CI vector
            cvecfile: Filename of CI vector file to write 
        """
        if not isinstance(orbs, np.ndarray) or len(orbs.shape) != 2:
            raise SyntaxError("Need a shaped NumPy array for write_cvecfile to do proper serialization for TeraChem.")

        ci_vector.astype(np.float64).tofile(orbfile)

    # Private kwarg helper function
    def _process_kwargs(self, job_options, **kwargs):
        """Process user-provided keyword arguments into a JobInput object
        
        Several keywords are processed by the client to set more complex fields
        in the Protobuf messages. These are:
            geom:               Sets job_options.mol.xyz from a list or NumPy array
            geom2:              Sets job_options.xyz2 from a list or NumPy array
            bond_order:         Sets job_options.return_bond_order to True or False
            cas_energy_labels:  Sets job_options.cas_energy_states and job_options.cas_energy_mults from a list of (state, mult) tuples
        All others are passed through as key-value pairs to the server, which will
        place them in the start file.
        Passing None to a previously set option will remove it from job_options

        Args:
            job_options: Target JobInput object
            **kwargs: Keyword arguments passed by user
        """
        for key, value in kwargs.iteritems():
            if key == 'geom':
                # Standard geometry, usually handled in other calling functions but here just in case
                if isinstance(value, np.ndarray):
                    value = value.flatten()
                if len(self.tc_options.mol.atoms) != len(value)/3.0:
                    raise ValueError("Geometry provided to geom does not match atom list")

                del job_options.mol.xyz[:]
                job_options.mol.xyz.extend(value)
            elif key == 'geom2':
                # Second geometry for ci_vec_overlap job
                if isinstance(value, np.ndarray):
                    value = value.flatten()
                if len(self.tc_options.mol.atoms) != len(value)/3.0:
                    raise ValueError("Geometry provided to geom2 does not match atom list")

                del job_options.xyz2[:]
                job_options.xyz2.extend(value)
            elif key == 'bond_order':
                # Request Meyer bond order matrix
                if value is not True and value is not False:
                    raise ValueError("Bond order request must be True or False")

                job_options.return_bond_order = value
            elif key == 'cas_energy_labels':
                state_labels = [label[0] for label in value]
                mult_labels = [label[1] for label in value]

                del job_options.cas_energy_states[:]
                del job_options.cas_energy_mults[:]
                job_options.cas_energy_states.extend(state_labels)
                job_options.cas_energy_mults.extend(mult_labels)
            elif key in job_options.user_options:
                # Overwrite currently defined custom user option
                index = job_options.user_options.index(key)
                if value is None:
                    del job_options.user_options[index:(index+1)]
                else:
                    job_options.user_options[index+1] = str(value)
            elif key not in job_options.user_options and value is not None:
                # New custom user option
                job_options.user_options.extend([key, str(value)])

    # Private send/recv functions
    def _send_msg(self, msg_type, msg_pb):
        """Sends a header + PB to the TeraChem Protobuf server (must be connected)

        Args:
            msg_type: Message type (defined as enum in protocol buffer)
            msg_pb: Protocol Buffer to send to the TCPB server
        """
        # This will always pack integers as 4 bytes since I am requesting a standard packing (big endian)
        # Big endian is convention for network byte order (because IBM or someone)
        if msg_pb is None:
            msg_size = 0
        else:
            msg_size = msg_pb.ByteSize()

        header = struct.pack('>II', msg_type, msg_size)
        try:
            self.tcsock.sendall(header)
        except socket.error as msg:
            raise RuntimeError("TCProtobufClient: Could not send header to {}. Error: {}".format(self.tcaddr, msg))

        msg_str = ''
        if msg_pb is not None:
            try:
                msg_str = msg_pb.SerializeToString()
                self.tcsock.sendall(msg_str)
            except socket.error as msg:
                raise RuntimeError("TCProtobufClient: Could not send protobuf to {}. Error: {}".format(self.tcaddr, msg))

        if self.trace:
            packet = header + msg_str
            self.outtracefile.write(packet)

    def _recv_msg(self, msg_type):
        """Receives a header + PB from the TeraChem Protobuf server (must be connected)

        Args:
            msg_type: Expected message type (defined as enum in protocol buffer)
        Returns Protocol Buffer of type msg_type (or None if no PB was sent)
        """
        # Receive header
        try:
            header = ''
            nleft = self.header_size
            while nleft:
                data = self.tcsock.recv(nleft)
                if data == '':
                    break
                header += data
                nleft -= len(data)

            # Check we got full message
            if nleft == self.header_size and data == '':
                raise RuntimeError("TCProtobufClient: Could not recv header from {} because socket was closed from server".format(self.tcaddr))
            elif nleft:
                raise RuntimeError("TCProtobufClient: Got {} of {} expected bytes for header from {}".format(nleft, self.header_size, self.tcaddr))
        except socket.error as msg:
            raise RuntimeError("TCProtobufClient: Could not recv header from {}. Error: {}".format(self.tcaddr, msg))

        msg_info = struct.unpack_from(">II", header)

        if msg_info[0] != msg_type:
            raise RuntimeError("TCProtobufClient: Received header for incorrect packet type. Expecting {} and got {}".format(msg_type, msg_info[0]))

        # Receive Protocol Buffer (if one was sent)
        if msg_info[1] >= 0:
            try:
                msg_str = ''
                nleft = msg_info[1] 
                while nleft:
                    data = self.tcsock.recv(nleft)
                    if data == '':
                        break
                    msg_str += data
                    nleft -= len(data)

                # Check we got full message
                if nleft == self.header_size and data == '':
                    raise RuntimeError("TCProtobufClient: Could not recv message from {} because socket was closed from server".format(self.tcaddr))
                elif nleft:
                    raise RuntimeError("TCProtobufClient: Got {} of {} expected bytes for header from {}".format(nleft, self.header_size, self.tcaddr))
            except socket.error as msg:
                raise RuntimeError("TCProtobufClient: Could not recv protobuf from {}. Error: {}".format(self.tcaddr, msg))

        if msg_type == pb.STATUS:
            recv_pb = pb.Status()
        elif msg_type == pb.MOL:
            recv_pb = pb.Mol()
        elif msg_type == pb.JOBINPUT:
            recv_pb = pb.JobInput()
        elif msg_type == pb.JOBOUTPUT:
            recv_pb = pb.JobOutput()
        else:
            raise RuntimeError("TCProtobufClient: Unknown message type {} for received message.".format(msg_type))

        recv_pb.ParseFromString(msg_str)

        if self.trace:
            packet = header + msg_str
            self.intracefile.write(packet)

        return recv_pb

