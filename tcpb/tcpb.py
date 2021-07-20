"""Simple Python socket client for communicating with TeraChem Protocol Buffer servers

Note that I (Stefan Seritan) have implemented a small protocol on top of the
protobufs since we send them in binary over TCP ALL MESSAGES ARE REQUIRED TO
HAVE AN 8 BYTE HEADER
First 4 bytes: int32 of protocol buffer message type (check the MessageType enum
in the protobuf file)
Second 4 bytes: int32 of packet size (not including the header)
"""

from __future__ import absolute_import, division, print_function

import logging
import socket
import struct
from time import sleep

import numpy as np
from qcelemental.models import AtomicInput, AtomicResult

from tcpb.utils import atomic_input_to_job_input, job_output_to_atomic_result

# Import the Protobuf messages generated from the .proto file
from . import terachem_server_pb2 as pb
from . import models
from .exceptions import ServerError
from .molden_constructor import tcpb_imd_fields2molden_string


logger = logging.getLogger(__name__)


class TCProtobufClient(object):
    """Connect and communicate with a TeraChem instance running in Protocol Buffer server mode
    (i.e. TeraChem was started with the -s|--server flag)
    """

    def __init__(self, host, port, debug=False, trace=False):
        """Initialize a TCProtobufClient object.

        Args:
            host (str): Hostname
            port (int): Port number (must be above 1023)
            debug (bool): If True, assumes connections work (used for testing with no server)
            trace (bool): If True, packets are saved to .bin files (which can then be used for testing)
        """
        self.debug = debug
        self.trace = trace
        if self.trace:
            self.intracefile = open("client_recv.bin", "wb")
            self.outtracefile = open("client_sent.bin", "wb")

        # Socket options
        self.update_address(host, port)
        self.tcsock = None
        # Would like to not hard code this, but the truth is I am expecting exactly 8 bytes, not whatever Python thinks 2 ints is
        self.header_size = 8

        self.prev_results = None

        self.curr_job_dir = None
        self.curr_job_scr_dir = None
        self.curr_job_id = None

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

    def update_address(self, host, port):
        """Update the host and port of a TCProtobufClient object.
        Note that you will have to call disconnect() and connect() before and after this
        yourself to actually connect to the new server.

        Args:
            host (str): Hostname
            port (int): Port number (must be above 1023)
        """
        # Sanity checks
        if not isinstance(host, str):
            raise TypeError("Hostname must be a string")
        if not isinstance(port, int):
            raise TypeError("Port number must be an integer")
        if port < 1023:
            raise ValueError(
                "Port number is not allowed to below 1023 (system reserved ports)"
            )

        # Socket options
        self.tcaddr = (host, port)

    def connect(self):
        """Connect to the TeraChem Protobuf server"""
        if self.debug:
            logging.info("in debug mode - assume connection established")
            return

        try:
            self.tcsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcsock.settimeout(60.0)  # Timeout of 1 minute
            self.tcsock.connect(self.tcaddr)
        except socket.error as msg:
            raise ServerError("Problem connecting to server: {}".format(msg), self)

    def disconnect(self):
        """Disconnect from the TeraChem Protobuf server"""
        if self.debug:
            logging.info("in debug mode - assume disconnection worked")
            return

        try:
            self.tcsock.shutdown(2)  # Shutdown read and write
            self.tcsock.close()
            self.tcsock = None
        except socket.error as msg:
            logger.error(
                f"Problem communicating with server: {self.tcaddr}. Disconnect assumed to have happened"
            )

    def is_available(self):
        """Asks the TeraChem Protobuf server whether it is available or busy through the Status protobuf message.
        Note that this does not reserve the server, and the status could change after this function is called.

        Returns:
            bool: True if the TeraChem PB server is currently available (no running job)
        """
        if self.debug:
            logging.info("in debug mode - assume terachem server is available")
            return True

        # Send Status message
        self._send_msg(pb.STATUS, None)

        # Receive Status header
        status = self._recv_msg(pb.STATUS)

        return not status.busy

    def compute(self, atomic_input: AtomicInput, interval: float = 0.5) -> AtomicResult:
        """Top level method for performing computations with QCSchema inputs/outputs"""
        # Create protobuf message
        job_input_msg = atomic_input_to_job_input(atomic_input)
        job_output = self.compute_pb(job_input_msg, interval)
        return job_output_to_atomic_result(
            atomic_input=atomic_input, job_output=job_output
        )

    def compute_py(
        self, job_input: models.JobInput, interval: float = 0.5
    ) -> models.JobOutput:
        """Top level method for performing computations using python objects"""
        job_input_msg = job_input.to_pb()
        job_output_msg = self.compute_pb(job_input_msg, interval)
        return models.JobOutput.from_pb(job_output_msg)

    def compute_pb(self, job_input: pb.JobInput, interval: float = 0.5) -> pb.JobOutput:
        """Top level method for performing computations using protocol buffer messages"""
        # Send message to server; retry until accepted
        self._send_msg(pb.JOBINPUT, job_input)
        status = self._recv_msg(pb.STATUS)
        while not status.accepted:
            print("JobInput not accepted. Retrying...")
            sleep(interval)
            self._send_msg(pb.JOBINPUT, job_input)
            status = self._recv_msg(pb.STATUS)
        print(status)
        while not self.check_job_complete():
            sleep(interval)

        return self._recv_msg(pb.JOBOUTPUT)

    def send_job_async(self, jobType="energy", geom=None, unitType="bohr", **kwargs):
        """Pack and send the current JobInput to the TeraChem Protobuf server asynchronously.
        This function expects a Status message back that either tells us whether the job was accepted.

        Args:
            jobType:    Job type key, as defined in the pb.JobInput.RunType enum (defaults to "energy")
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to "bohr")
            **kwargs:   Additional TeraChem keywords, check models.JobInput.from_stefan_style_dict() for behaviour

        Returns:
            bool: True on job acceptance, False on server busy, and errors out if communication fails
        """
        if jobType.upper() not in list(pb.JobInput.RunType.keys()):
            raise ValueError(
                "Job type specified is not available in this version of the TCPB client\n"
                "Allowed run types: {}".format(list(pb.JobInput.RunType.keys()))
            )
        if geom is None:
            raise SyntaxError("Did not provide geometry to send_job_async()")
        if isinstance(geom, np.ndarray):
            geom = geom.flatten()
        if unitType.upper() not in list(pb.Mol.UnitType.keys()):
            raise ValueError(
                "Unit type specified is not available in this version of the TCPB client\n"
                "Allowed unit types: {}".format(list(pb.Mol.UnitType.keys()))
            )

        if self.debug:
            logging.info("in debug mode - assume job completed")
            return True

        # Job setup
        job_input_msg = self._create_job_input_msg(jobType, geom, unitType, **kwargs)

        self._send_msg(pb.JOBINPUT, job_input_msg)

        status_msg = self._recv_msg(pb.STATUS)

        if status_msg.WhichOneof("job_status") == "accepted":
            self._set_status(status_msg)

            return True
        else:
            return False

    def _set_status(self, status_msg: pb.Status):
        """Sets status on self if job is accepted"""
        self.curr_job_dir = status_msg.job_dir
        self.curr_job_scr_dir = status_msg.job_scr_dir
        self.curr_job_id = status_msg.server_job_id

    def _create_job_input_msg(self, jobType, geom, unitType="bohr", **kwargs):
        """Method for setting up jobs according to old mechanism

        Refactored this method out to allow for better testing
        """
        job_input_msg = \
            models.JobInput.from_stefan_style_dict(jobType, geom, unitType, **kwargs)\
                .to_pb()

        return job_input_msg

    def check_job_complete(self):
        """Pack and send a Status message to the TeraChem Protobuf server asynchronously.
        This function expects a Status message back with either working or completed set.
        Errors out if just busy message returned, implying the job we are checking was not submitted
        or had some other issue

        Returns:
            bool: True if job is completed, False otherwise
        """
        print("Checking jobs status...")
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
            raise ServerError(
                "Invalid or no job status received, either no job submitted before check_job_complete() or major server issue",
                self,
            )

    def recv_job_async(self):
        """Recv and unpack a JobOutput message from the TeraChem Protobuf server asynchronously.
        This function expects the job to be ready (i.e. check_job_complete() returned true),
        so will error out on timeout.

        Returns:
            dict: Results as described in models.JobOutput.to_stefan_style_dict()
        """
        output = self._recv_msg(pb.JOBOUTPUT)
        results = models.JobOutput.from_pb(output).to_stefan_style_dict()

        # Save results for user access later
        self.prev_results = results

        # Wipe state
        self.curr_job_dir = None
        self.curr_job_scr_dir = None
        self.curr_job_id = None

        return results

    def compute_job_sync(self, jobType="energy", geom=None, unitType="bohr", **kwargs):
        """Wrapper for send_job_async() and recv_job_async(), using check_job_complete() to poll the server.

        Args:
            jobType:    Job type key, as defined in the pb.JobInput.RunType enum (defaults to 'energy')
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check models.JobInput.from_stefan_style_dict() for behaviour

        Returns:
            dict: Results mirroring recv_job_async
        """
        if self.debug:
            logging.info(
                "in debug mode - assume compute_job_sync completed successfully"
            )
            return True

        accepted = self.send_job_async(jobType, geom, unitType, **kwargs)
        while accepted is False:
            sleep(0.5)
            accepted = self.send_job_async(jobType, geom, unitType, **kwargs)

        completed = self.check_job_complete()
        while completed is False:
            sleep(0.5)
            completed = self.check_job_complete()

        return self.recv_job_async()

    # CONVENIENCE FUNCTIONS #
    def compute_energy(self, geom=None, unitType="bohr", **kwargs):
        """Compute energy of a new geometry, but with the same atom labels/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check models.JobInput.from_stefan_style_dict() for behaviour

        Returns:
            float: Energy
        """
        results = self.compute_job_sync("energy", geom, unitType, **kwargs)
        return results["energy"]

    def compute_gradient(self, geom=None, unitType="bohr", **kwargs):
        """Compute gradient of a new geometry, but with the same atom labels/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check models.JobInput.from_stefan_style_dict() for behaviour

        Returns:
            tuple: Tuple of (energy, gradient)
        """
        results = self.compute_job_sync("gradient", geom, unitType, **kwargs)
        return results["energy"], results["gradient"]

    # Convenience to maintain compatibility with NanoReactor2
    def compute_forces(self, geom=None, unitType="bohr", **kwargs):
        """Compute forces of a new geometry, but with the same atoms labels/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check models.JobInput.from_stefan_style_dict() for behaviour

        Returns:
            tuple: Tuple of (energy, forces), which is really (energy, -gradient)
        """
        results = self.compute_job_sync("gradient", geom, unitType, **kwargs)
        return results["energy"], -1.0 * results["gradient"]

    def compute_coupling(self, geom=None, unitType="bohr", **kwargs):
        """Compute nonadiabatic coupling of a new geometry, but with the same atoms labels/charge/spin
        multiplicity and wave function format as the previous calculation.

        Args:
            geom:       Cartesian geometry of the new point
            unitType:   Unit type key, as defined in the pb.Mol.UnitType enum (defaults to 'bohr')
            **kwargs:   Additional TeraChem keywords, check models.JobInput.from_stefan_style_dict() for behaviour

        Returns:
            (num_atoms, 3) ndarray: Nonadiabatic coupling vector
        """
        results = self.compute_job_sync("coupling", geom, unitType, **kwargs)
        return results["nacme"]

    def compute_ci_overlap(
        self,
        geom=None,
        geom2=None,
        cvec1file=None,
        cvec2file=None,
        orb1afile=None,
        orb1bfile=None,
        orb2afile=None,
        orb2bfile=None,
        unitType="bohr",
        **kwargs,
    ):
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
            **kwargs:   Additional TeraChem keywords, check models.JobInput.from_stefan_style_dict() for behaviour

        Returns:
            (num_states, num_states) ndarray: CI vector overlaps
        """
        if geom is None or geom2 is None:
            raise SyntaxError("Did not provide two geometries to compute_ci_overlap()")
        if cvec1file is None or cvec2file is None:
            raise SyntaxError("Did not provide two CI vectors to compute_ci_overlap()")
        if orb1afile is None or orb1bfile is None:
            raise SyntaxError(
                "Did not provide two sets of orbitals to compute_ci_overlap()"
            )
        if (
            (orb1bfile is not None and orb2bfile is None)
            or (orb1bfile is None and orb2bfile is not None)
            and kwargs["closed_shell"] is False
        ):
            raise SyntaxError(
                "Did not provide two sets of open-shell orbitals to compute_ci_overlap()"
            )
        elif (
            orb1bfile is not None
            and orb2bfile is not None
            and kwargs["closed_shell"] is True
        ):
            print(
                "WARNING: System specified as closed, but open-shell orbitals were passed to compute_ci_overlap(). Ignoring beta orbitals."
            )

        if kwargs["closed_shell"]:
            results = self.compute_job_sync(
                "ci_vec_overlap",
                geom,
                unitType,
                geom2=geom2,
                cvec1file=cvec1file,
                cvec2file=cvec2file,
                orb1afile=orb1afile,
                orb2afile=orb2afile,
                **kwargs,
            )
        else:
            raise RuntimeError(
                "WARNING: Open-shell systems are currently not supported for overlaps"
            )
            # results = self.compute_job_sync("ci_vec_overlap", geom, unitType, geom2=geom2,
            #    cvec1file=cvec1file, cvec2file=cvec2file,
            #    orb1afile=orb1afile, orb1bfile=orb1bfile,
            #    orb2afile=orb1bfile, orb2bfile=orb2bfile, **kwargs)

        return results["ci_overlap"]

    # Private send/recv functions
    def _send_msg(self, msg_type, msg_pb=None):
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

        header = struct.pack(">II", msg_type, msg_size)
        try:
            self.tcsock.sendall(header)
        except socket.error as msg:
            raise ServerError("Could not send header: {}".format(msg), self)

        msg_str = b""
        if msg_pb is not None:
            try:
                msg_str = msg_pb.SerializeToString()
                self.tcsock.sendall(msg_str)
            except socket.error as msg:
                raise ServerError("Could not send protobuf: {}".format(msg), self)

        if self.trace:
            packet = header + msg_str
            self.outtracefile.write(packet)

    def _recv_msg(self, msg_type):  # noqa NOTE: C901 too complex!
        """Receives a header + PB from the TeraChem Protobuf server (must be connected)

        Args:
            msg_type: Expected message type (defined as enum in protocol buffer)

        Returns:
            protobuf: Protocol Buffer of type msg_type (or None if no PB was sent)
        """
        # Receive header
        try:
            header = b""
            nleft = self.header_size
            while nleft:
                data = self.tcsock.recv(nleft)
                if data == b"":
                    break
                header += data
                nleft -= len(data)

            # Check we got full message
            if nleft == self.header_size and data == b"":
                raise ServerError(
                    "Could not recv header because socket was closed from server", self
                )
            elif nleft:
                raise ServerError(
                    "Recv'd {} of {} expected bytes for header".format(
                        nleft, self.header_size
                    ),
                    self,
                )
        except socket.error as msg:
            raise ServerError("Could not recv header: {}".format(msg), self)

        msg_info = struct.unpack_from(">II", header)

        if msg_info[0] != msg_type:
            raise ServerError(
                "Received header for incorrect packet type (expecting {} and got {})".format(
                    msg_type, msg_info[0]
                ),
                self,
            )

        # Receive Protocol Buffer (if one was sent)
        if msg_info[1] >= 0:
            try:
                msg_str = b""
                nleft = msg_info[1]
                while nleft:
                    data = self.tcsock.recv(nleft)
                    if data == b"":
                        break
                    msg_str += data
                    nleft -= len(data)

                # Check we got full message
                if nleft == self.header_size and data == b"":
                    raise ServerError(
                        "Could not recv message because socket was closed from server",
                        self,
                    )
                elif nleft:
                    raise ServerError(
                        "Recv'd {} of {} expected bytes for protobuf".format(
                            nleft, msg_info[1]
                        ),
                        self,
                    )
            except socket.error as msg:
                raise ServerError("Could not recv protobuf: {}".format(msg), self)

        if msg_type == pb.STATUS:
            recv_pb = pb.Status()
        elif msg_type == pb.MOL:
            recv_pb = pb.Mol()
        elif msg_type == pb.JOBINPUT:
            recv_pb = pb.JobInput()
        elif msg_type == pb.JOBOUTPUT:
            recv_pb = pb.JobOutput()
        else:
            raise ServerError(
                "Unknown message type {} for received message.".format(msg_type), self
            )

        recv_pb.ParseFromString(msg_str)

        if self.trace:
            packet = header + msg_str
            self.intracefile.write(packet)

        return recv_pb
