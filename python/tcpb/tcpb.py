# Simple Python socket client class
# Used for communicating with TeraChem over protocol buffers

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

# Helper functions, mainly used to facilitate testing
from .pbhelper import save_pb


class TCProtobufClient(object):
    """Connect and communicate with a TeraChem instance running in Protocol Buffer server mode
    (i.e. TeraChem was started with the -s|--server flag)
    """
    def __init__(self, host, port, debug=False, trace=False,
                 atoms=None, charge=0, spinmult=1, closed=None, restricted=None,
                 method=None, basis=None, **kwargs):
        """Initialize a TCProtobufClient object.

        Args:
            host: String of hostname
            port: Integer of port number (must be above 1023)
            debug: If True, assumes connections work (used for testing with no server)
            trace: If True, pbhelper.save_pb() is used to save a full Protobuf trace for testing
            atoms: List of atoms types as strings
            charge: Total charge (int)
            spinmult: Spin multiplicity (int)
            closed: Whether to run as closed-shell (bool)
            restricted: Whether to run as restricted (bool)
            method: TeraChem method (string)
            basis: TeraChem basis (string)
            **kwargs: Additional TeraChem keywords (dict of key-value pairs as strings)
        """
        self.debug = debug
        self.trace = trace

        # Sanity checks
        if method is None:
            raise SyntaxError("TeraChem method is required by client")
        elif not isinstance(method, basestring):
            raise TypeError("TeraChem method must be a string")
        elif method.upper() not in pb.JobInput.MethodType.keys():
            raise ValueError("Method specified is not available in this version of the TeraChem Protobuf server")
        if basis is None:
            raise SyntaxError("TeraChem basis is required by client")
        elif not isinstance(basis, basestring):
            raise TypeError("TeraChem basis must be a string")

        # Socket options
        self.update_address(host, port)
        self.tcsock = None
        # Would like to not hard code this, but the truth is I am expecting exactly 8 bytes, not whatever Python thinks 2 ints is
        self.headerSize = 8

        # Store options directly in Protobufs
        self.tc_options = pb.JobInput()
        # Since protobuf defaults to not None ([], 0, False, etc.), I have to explicitly check whether things were set by the user
        self.atoms_set = False
        self.charge_set = False
        self.spinmult_set = False
        self.closed_set = False
        self.restricted_set = False
        self.method_set = False
        self.basis_set = False
        self.update_options(atoms, charge, spinmult, closed, restricted, method, basis, **kwargs)

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

    def setup(self, mol, closed=None, restricted=None):
        """Convenience routine to setup molecular parameters using a molecule object.

        Args:
            mol:    A molecule object similar to core.molecule.Molecule that have fields
                    `atoms`, `charge` and `multiplicity`
        """
        # Check if mol contains all proper fields
        if not set(['atoms', 'charge', 'multiplicity']).issubset(set(dir(mol))):
            raise AttributeError("Invalid argument to setup(). "
                                 "Attributes atoms, charge and multiplicity are required")

        self.update_options(mol.atoms, mol.charge, mol.multiplicity, closed, restricted)

    def update_options(self, atoms=None, charge=None, spinmult=None, closed=None, restricted=None,
                       method=None, basis=None, **kwargs):
        """Update the TeraChem options of a TCProtobufClient object.
        If an argument is passed as None, the value does not change.
        If a molecule option or basis is changed, TeraChem will regenerate MOs on next job.

        Args:
            atoms:      List of atoms types as strings
            charge:     Total charge (int)
            spinmult:   Spin multiplicity (int)
            closed:     Whether to run as closed-shell (bool)
            restricted: Whether to run as restricted (bool)
            method:     TeraChem method (string)
            basis:      TeraChem basis (string)
            **kwargs:   Additional TeraChem keywords. Passing None as the value will wipe that keyword
                        from the options of all future jobs
                        Keywords that will be handled by the client:
                        bond_order=True will return Meyer bond order matrix
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
            if closed is None and self.tc_options.mol.closed is True and spinmult != 1:
                print("WARNING: Spin multiplicity greater than 1 but molecule set as closed, setting closed to False")
                closed = False
            if closed is True and spinmult != 1:
                print("WARNING: Molecule cannot be closed with a spin multiplicity greater than 1, setting closed to False")
                closed = False
            if restricted is None and self.tc_options.mol.restricted is True and spinmult != 1:
                print("WARNING: Spin multiplicity greater than 1 but molecule set as restricted, setting restricted to False")
                restricted = False
            if restricted is True and spinmult != 1:
                print("WARNING: Cannot specify restricted with a spin multiplicity greater than 1, setting restricted to False")
                restricted = False
        if closed is not None and not isinstance(closed, bool):
            raise TypeError("Closed must be either True or False")
        if restricted is not None and not isinstance(restricted, bool):
            raise TypeError("Closed must be either True or False")
        if closed is True and restricted is False:
            print("WARNING: Cannot have a closed unrestricted system, setting to closed to False")
            closed = False

        if method is not None:
            if not isinstance(method, basestring):
                raise TypeError("TeraChem method must be a string")
            elif method.upper() not in pb.JobInput.MethodType.keys():
                raise ValueError("Method specified is not available in this version of the TeraChem Protobuf server")
        if basis is not None:
            if not isinstance(basis, basestring):
                raise TypeError("TeraChem basis must be a string")

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
        if closed is not None:
            self.tc_options.mol.closed = closed
            self.closed_set = True
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
           closed is not None or restricted is not None or method is not None or basis is not None:
            del self.tc_options.guess_mo_coeffs_a[:]
            del self.tc_options.guess_mo_coeffs_b[:]

        for key, value in kwargs.iteritems():
            if key == 'bond_order':
                self.tc_options.return_bond_order = value
            elif key in self.tc_options.user_options:
                index = self.tc_options.user_options.index(key)
                if value is None:
                    del self.tc_options.user_options[index:(index+1)]
                else:
                    self.tc_options.user_options[index+1] = str(value)
            elif key not in self.tc_options.user_options and value is not None:
                self.tc_options.user_options.extend([key, str(value)])

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
            self.tcsock.settimeout(5.0)  # Timeout of 5 seconds
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

        # Send Status header
        self._send_header(pb.STATUS, 0)
        if self.trace:
            save_pb(pb.STATUS, None, "sent_pb.dat", True)

        # Receive Status header
        try:
            header = self._recv_header()
        except socket.error as msg:
            raise RuntimeError("TCProtobufClient: Problem receiving Status header for response in is_available(). Error: {}".
                               format(msg))
        if header is None or header[0] != pb.STATUS:
            raise RuntimeError("TCProtobufClient: Did not receive proper response from server for is_available(). Header: {}".
                               format(header))

        try:
            msgStr = self._recv_message(header[1])
        except socket.error as msg:
            raise RuntimeError("TCProtobufClient: Problem receiving Status protobuf for response in is_available(). Error: {}".
                               format(msg))

        status = pb.Status()
        status.ParseFromString(msgStr)

        if self.trace:
            save_pb(pb.STATUS, status, "recv_pb.dat", True)

        return not status.busy

    def send_job_async(self, jobType=pb.JobInput.ENERGY, geom=None, units=pb.Mol.BOHR, **kwargs):
        """Pack and send the current JobInput to the TeraChem Protobuf server asynchronously.
        This function expects a Status message back that either tells us whether the job was accepted.

        Args:
            jobType:    Job type as defined in the pb.JobInput.RunType enum (defaults to RunType.ENERGY)
            geom:       Cartesian geometry of the new point
            units:      Units as defined in the pb.Mol.UnitType enum (defaults to UnitType.BOHR)
            **kwargs:   Additional TeraChem keywords, overriding the default job options. For more info, look at update_options()

        Returns True on job acceptance, False on server busy, and errors out if communication fails
        """
        # Check if previous molecule setup is available
        if self.atoms_set is False:
            raise LookupError("send_job_async() called before atoms were set.")
        if self.charge_set is False:
            raise LookupError("send_job_async() called before charge was set.")
        if self.spinmult_set is False:
            raise LookupError("send_job_async() called before spin multiplicity was set.")
        if self.closed_set is False:
            raise LookupError("send_job_async() called before closed was set.")
        if self.restricted_set is False:
            raise LookupError("send_job_async() called before restricted was set.")
        if self.method_set is False:
            raise LookupError("send_job_async() called before method was set.")
        if self.basis_set is False:
            raise LookupError("send_job_async() called before basis was set.")
        if geom is None:
            raise SyntaxError("Did not provide geometry to send_job_async()")
        if isinstance(geom, np.ndarray):
            geom = geom.flatten()
        if len(self.tc_options.mol.atoms) != len(geom)/3.0:
            raise ValueError("Geometry does not match atom list in send_job_async()")
        if units not in pb.Mol.UnitType.values():
            # TODO: Could actually check real enum values here, would be more future proof that way
            raise ValueError("Not allowed unit type. Only Angstrom (0) and Bohr (1) are allowed")

        if self.debug:
            logging.info("in debug mode - assume job completed")
            return True

        # Job setup
        del self.tc_options.mol.xyz[:]
        self.tc_options.mol.xyz.extend(geom)
        self.tc_options.mol.units = units
        self.tc_options.run = jobType

        # Handle kwargs for this specific job
        job_options = pb.JobInput()
        job_options.CopyFrom(self.tc_options)

        for key, value in kwargs.iteritems():
            if key == 'bond_order':
                job_options.return_bond_order = value
            elif key in job_options.user_options:
                index = job_options.user_options.index(key)
                if value is None:
                    del job_options.user_options[index:(index+1)]
                else:
                    job_options.user_options[index+1] = str(value)
            elif key not in job_options.user_options and value is not None:
                job_options.user_options.extend([key, str(value)])

        self._send_header(pb.JOBINPUT, job_options.ByteSize())

        msgStr = job_options.SerializeToString()
        self.tcsock.sendall(msgStr)

        if self.trace:
            save_pb(pb.JOBINPUT, job_options, "sent_pb.dat", True)

        # Handle response
        try:
            header = self._recv_header()
        except socket.error as msg:
            raise RuntimeError("TCProtobufClient: Problem receiving Status header for response in send_job_async(). Error: {}".
                               format(msg))
        if header is None or header[0] != pb.STATUS:
            raise RuntimeError("TCProtobufClient: Did not receive proper response from server for send_job_async(). Header: {}".
                               format(header))

        try:
            msgStr = self._recv_message(header[1])
        except socket.error as msg:
            raise RuntimeError("TCProtobufClient: Problem receiving Status protobuf for response in send_job_async. Error: {}".
                               format(msg))

        status = pb.Status()
        status.ParseFromString(msgStr)

        if self.trace:
            save_pb(pb.STATUS, status, "recv_pb.dat", True)

        if status.WhichOneof("job_status") == "accepted":
            return True
        else:
            return False

    def check_job_complete(self):
        """Pack and send a Status message to the TeraChem Protobuf server asynchronously.
        This function expects a Status message back with either working or completed set.
        Errors out if just busy message returned, implying the job we are checking was not submitted or had some other issue

        Returns True if job is completed, False otherwise
        """

        if self.debug:
            logging.info("in debug mode - assume check_job_complete is True")
            return True

        # Send Status header
        self._send_header(pb.STATUS, 0)

        if self.trace:
            save_pb(pb.STATUS, None, "sent_pb.dat", True)

        # Receive Status header
        try:
            header = self._recv_header()
        except socket.error as msg:
            raise RuntimeError(
                "TCProtobufClient: Problem receiving Status header for response in check_job_complete(). Error: {}".
                format(msg))
        if header is None or header[0] != pb.STATUS:
            raise RuntimeError(
                "TCProtobufClient: Did not receive proper response from server for check_job_complete(). Header: {}".
                format(header))

        try:
            msgStr = self._recv_message(header[1])
        except socket.error as msg:
            raise RuntimeError(
                "TCProtobufClient: Problem receiving Status protobuf for response in check_job_complete(). Error: {}".
                format(msg))

        status = pb.Status()
        status.ParseFromString(msgStr)

        if self.trace:
            save_pb(pb.STATUS, status, "recv_pb.dat", True)

        if status.WhichOneof("job_status") == "completed":
            return True
        elif status.WhichOneof("job_status") == "working":
            return False
        else:
            raise RuntimeError("TCProtobufClient: No valid job status received in check_job_complete(),\
                                either no job submitted or major issue with server.")

    def recv_job_async(self):
        """Recv and unpack a JobOutput message from the TeraChem Protobuf server asynchronously.
        This function expects the job to be ready (i.e. check_job_complete() returned true), so will error out on timeout.

        Returns a results dictionary that mirrors the JobOutput message, using NumPy arrays when possible
        """
        # Receive JobOutput
        try:
            header = self._recv_header()
        except socket.error as msg:
            raise RuntimeError(
                "TCProtobufClient: Problem receiving Status header for response in recv_job_async(). Error: {}".
                format(msg))
        if header is None or header[0] != pb.JOBOUTPUT:
            raise RuntimeError(
                "TCProtobufClient: Did not receive proper response from server for recv_job_async(). Header: {}".
                format(header))

        try:
            msgStr = self._recv_message(header[1])
        except socket.error as msg:
            raise RuntimeError(
                "TCProtobufClient: Problem receiving Status protobuf for response in recv_job_async(). Error: {}".
                format(msg))

        output = pb.JobOutput()
        output.ParseFromString(msgStr)

        if self.trace:
            save_pb(pb.JOBOUTPUT, output, "recv_pb.dat", True)

        # Set MOs for next job
        del self.tc_options.guess_mo_coeffs_a[:]
        del self.tc_options.guess_mo_coeffs_b[:]
        self.tc_options.guess_mo_coeffs_a.extend(output.mo_coeffs_a)
        self.tc_options.guess_mo_coeffs_b.extend(output.mo_coeffs_b)

        # Parse output into normal python dictionary
        results = {
            'atoms'         : np.array(output.mol.atoms, dtype='S2'),
            'geom'          : np.array(output.mol.xyz).reshape(-1, 3),
            'energy'        : output.energy,
            'gradient'      : np.array(output.gradient).reshape(-1, 3),
            'charges'       : np.array(output.charges),
            'spins'         : np.array(output.spins),
            'dipole_moment' : output.dipoles[3],
            'dipole_vector' : np.array(output.dipoles[:3]),
            'job_dir'       : output.job_dir,
        }

        nOrbs = int(np.sqrt(len(output.mo_coeffs_a)))
        if output.mol.restricted is True:
            results['mo_coeffs'] = np.array(output.mo_coeffs_a).reshape(nOrbs, nOrbs)
        else:
            results['mo_coeffs_a'] = np.array(output.mo_coeffs_a).reshape(nOrbs, nOrbs)
            results['mo_coeffs_b'] = np.array(output.mo_coeffs_b).reshape(nOrbs, nOrbs)

        if len(output.bond_order):
            nAtoms = len(output.mol.atoms)
            results['bond_order'] = np.array(output.bond_order).reshape(nAtoms, nAtoms)

        # Save results for user access later
        self.prev_results = results

        return results

    def compute_job_sync(self, jobType=pb.JobInput.ENERGY, geom=None, units=pb.Mol.BOHR, **kwargs):
        """Wrapper for send_job_async() and recv_job_async(), using check_job_complete() to poll the server.

        Args:
            jobType:    Job type as defined in the pb.JobInput.RunType enum (defaults to RunType.ENERGY)
            geom:       Cartesian geometry of the new point
            units:      Units as defined in the pb.Mol.UnitType enum (defaults to UnitType.BOHR)
            **kwargs:   Additional TeraChem keywords, overriding the default job options. For more info, look at update_options()

        Returns a results dictionary that mirrors the JobOutput message, using NumPy arrays when possible
        """
        if self.debug:
            logging.info("in debug mode - assume compute_job_sync completed successfully")
            return True

        accepted = self.send_job_async(jobType, geom, units, **kwargs)
        while accepted is False:
            accepted = self.send_job_async(jobType, geom, units, **kwargs)

        completed = self.check_job_complete()
        while completed is False:
            completed = self.check_job_complete()

        return self.recv_job_async()

    # CONVENIENCE FUNCTIONS #
    def compute_energy(self, geom=None, units=pb.Mol.BOHR):
        """Compute energy of a new geometry, but with the same atoms/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:   Cartesian geometry of the new point
            units:  Units as defined in the pb.Mol.UnitType enum (defaults to UnitType.BOHR)

        Returns energy
        """
        results = self.compute_job_sync(pb.JobInput.ENERGY, geom, units)
        return results['energy']

    def compute_gradient(self, geom=None, units=pb.Mol.BOHR):
        """Compute gradient of a new geometry, but with the same atoms/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:   Cartesian geometry of the new point
            units:  Units as defined in the pb.Mol.UnitType enum (defaults to UnitType.BOHR)

        Returns a tuple of (energy, gradient)
        """
        results = self.compute_job_sync(pb.JobInput.GRADIENT, geom, units)
        return results['energy'], results['gradient']

    # Convenience to maintain compatibility with NanoReactor2
    def compute_forces(self, geom=None, units=pb.Mol.BOHR):
        """Compute forces of a new geometry, but with the same atoms/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:   Cartesian geometry of the new point
            units:  Units as defined in the pb.Mol.UnitType enum (defaults to UnitType.BOHR)

        Returns a tuple of (energy, forces), which is really (energy, -gradient)
        """
        results = self.compute_job_sync(pb.JobInput.GRADIENT, geom, units)
        return results['energy'], -1.0*results['gradient']

    # Private send/recv functions
    def _send_header(self, msgType, msgSize):
        """Sends a header to the TeraChem Protobuf server (must be connected)

        Args:
            msgSize: Size of following message (not including header)
            msgType: Message type (defined as enum in protocol buffer)
        Returns True if send was successful, False otherwise
        """
        # This will always pack integers as 4 bytes since I am requesting a standard packing (big endian)
        # Big endian is convention for network byte order (because IBM or someone)
        header = struct.pack('>II', msgType, msgSize)
        try:
            self.tcsock.sendall(header)
        except socket.error as msg:
            print("TCProtobufClient: Could not send header to {}. Error: {}".format(self.tcaddr, msg))
            return False

        return True

    def _recv_header(self):
        """Receive a header from the TeraChem Protobuf server (must be connected)

        Args: None
        Returns (msgType, msgSize) on successful recv, None otherwise
        """
        headerStr = ''
        nleft = self.headerSize
        while nleft:
            data = self.tcsock.recv(nleft)
            if data == '':
                break
            headerStr += data
            nleft -= len(data)

        # Check we got full message
        if nleft == self.headerSize and data == '':
            print("TCProtobufClient: Could not recv header from {} because socket was closed from server".format(self.tcaddr))
            return None
        elif nleft:
            print("TCProtobufClient: Got {} of {} expected bytes for header from {}".format(nleft, self.headerSize, self.tcaddr))
            return None

        msgInfo = struct.unpack_from(">II", headerStr)
        return msgInfo

    def _recv_message(self, msgSize):
        """Receive a message from the TeraChem Protobuf server (must be connected)

        Args:
            msgSize: Integer of message size
        Returns a string representation of the binary message if successful, None otherwise
        """
        if msgSize == 0:
            return ""

        msgStr = ''
        nleft = msgSize
        while nleft:
            data = self.tcsock.recv(nleft)
            if data == '':
                break
            msgStr += data
            nleft -= len(data)

        # Check we got full message
        if nleft == self.headerSize and data == '':
            print("TCProtobufClient: Could not recv message from {} because socket was closed from server".format(self.tcaddr))
            return None
        elif nleft:
            print("TCProtobufClient: Got {} of {} expected bytes for header from {}".format(nleft, self.headerSize, self.tcaddr))
            return None

        return msgStr
