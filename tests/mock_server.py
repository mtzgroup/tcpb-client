#!/usr/bin/env python
# mock_server.py
# Written by Stefan Seritan on July 16th, 2017
#
# A mock server for TCPB client testing
# Communication is really over sockets, but responses are feed into the mock server beforehand
# Threading model from https://stackoverflow.com/questions/23828264/how-to-make-a-simple-multithreaded-socket-server-in-python-that-remembers-client

import numpy as np
import socket
import struct
from threading import Thread
from Queue import Queue

from tcpb import terachem_server_pb2 as pb
from . import pbhelper


class MockServer(object):
    """Mock server for TCPB client testing

    Intended testing workflow:
    - Response state of MockServer is set
    - Client call is executed and communicated to mock server over socket
    - Response is sent back to client over socket (on listening thread)
    - Output of client function is tested for correctness
    """
    def __init__(self, port, intracefile, outtracefile):
        """Initialize the MockServer object.

        Args:
            port: Integer of port number
            intracefile: Binary file containing packets recv'd by client
            outtracefile: Binary file containing packets sent by client
        """
        # Sanity checks
        if not isinstance(port, int):
            raise TypeError("Port number must be an integer")
        if port < 1023:
            raise ValueError("Port number is not allowed to below 1023 (system reserved ports)")

        self.header_size = 8 #Expect exactly 2 ints of 4 bytes each
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('localhost', port))
        self.active_listening = True
        self.client_threads = []

        # Expected messages from client (out for client, in for server)
        self.expected_queue = Queue()
        self.set_expected_messages(outtracefile)

        # Response message for client (in for client, out for server)
        self.response_queue = Queue()
        self.set_response_messages(intracefile)

    def set_expected_messages(self, tracefile):
        """Add messages to the expected messages queue

        Args:
            tracefile: Binary file containing packets sent by client (and therefore recv'd by server)
        """
        msgs = pbhelper.load_trace(tracefile)
        for m in msgs:
            self.expected_queue.put(m)

    def set_response_messages(self, tracefile):
        """Add messages to the response messages queue

        Args:
            tracefile: Binary file containing packets recv'd by client (and therefore sent by server)
        """
        msgs = pbhelper.load_trace(tracefile)
        for m in msgs:
            self.response_queue.put(m)

    def listen(self):
        self.sock.listen(5)
        while self.active_listening:
            client, address = self.sock.accept()
            client.settimeout(60)
            t = Thread(target=self.testClient, args=(client, address))
            t.start()
            self.client_threads += [t]

    def testClient(self, client, address):    
        if self.expected_queue.qsize() != self.response_queue.qsize():
            raise RuntimeError("Expected and response queues are not the same size")

        # Handle getting message from client
        # Slightly brittle because I only wait one minute, but should be fine for testing
        try:
            header = self._recv_header(client)
        except socket.error as msg:
            raise RuntimeError("MockServer: Problem receiving header from client. Error: {}".format(msg))

        if header is None:
            raise RuntimeError("MockServer: Problem receiving header from client")

        expected_msg = self.expected_queue.get(False)
        expected_header = (expected_msg[0], expected_msg[1].ByteSize())
        if header != expected_header:
            raise RuntimeError("MockServer: Did not receive expected header from client")

        try:
            msg_str = self._recv_message(client, header[1])
        except socket.error as msg:
            raise RuntimeError("MockServer: Problem receiving message from client. Error: {}".format(msg))

        # TODO: Test protobuf is the same
        if expected_msg[0] == pb.STATUS:
            recvd_pb = pb.Status()
        elif expected_msg[0] == pb.MOL:
            recvd_pb = pb.Mol()
        elif expected_msg[0] == pb.JOBINPUT:
            recvd_pb = pb.JobInput()
        elif expected_msg[0] == pb.JOBOUTPUT:
            recvd_pb = pb.JobOutput()
        else:
            raise RuntimeError("MockServer: Unknown protobuf type")

        recvd_pb.ParseFromString(expected_msg[1])
        pbhelper.compare_pb(expected_msg

        # Send response
        try:
            self._send_header(client, self.response_header[0], self.response_header[1])
        except socket.error as msg:
            raise RuntimeError("MockServer: Problem sending header to client. Error: {}".format(msg))

        try:
            self._send_message(client, self.response_pb.SerializeToString())
        except socket.error as msg:
            raise RuntimeError("MockServer: Problem sending message to client. Error: {}".format(msg))

        client.shutdown(2)
        client.close()

    def shutdown(self):
        self.active_listening = False
        for t in self.client_threads:
            t.join()

    # Private send/recv functions
    def _send_header(self, client, msg_type, msg_size):
        """Sends a header to the TCPBClient

        Args:
            client: Client socket
            msg_size: Size of following message (not including header)
            msg_type: Message type (defined as enum in protocol buffer)
        Returns True if send was successful, False otherwise
        """
        # This will always pack integers as 4 bytes since I am requesting a standard packing (big endian)
        # Big endian is convention for network byte order (because IBM or someone)
        header = struct.pack('>II', msg_type, msg_size)
        try:
            client.sendall(header)
        except socket.error as msg:
            print("MockServer: Could not send header. Error: {}".format(msg))
            return False

        return True

    def _send_message(self, client, msg_str):
        """Sends a header to the TCPBClient

        Args:
            client: Client socket
            msg_str: String representation of binary message
        Returns True if send was successful, False otherwise
        """
        try:
            client.sendall(msg_str)
        except socket.error as msg:
            print("MockServer: Could not send message. Error: {}".format(msg))
            return False

        return True

    def _recv_header(self, client):
        """Receive a header from the TCPBClient

        Args:
            client: Client socket
        Returns (msg_type, msg_size) on successful recv, None otherwise
        """
        header = ''
        nleft = self.header_size
        while nleft:
            data = client.recv(nleft)
            if data == '':
                break
            header += data
            nleft -= len(data)

        # Check we got full message
        if nleft == self.header_size and data == '':
            print("MockServer: Could not recv header because socket was closed from client")
            return None
        elif nleft:
            print("MockServer: Got {} of {} expected bytes for header".format(nleft, self.header_size)
            return None

        msg_info = struct.unpack_from(">II", header)
        return msg_info

    def _recv_message(self, client, msg_size):
        """Receive a message from the TCPBClient

        Args:
            client: Client socket
            msg_size: Integer of message size
        Returns a string representation of the binary message if successful, None otherwise
        """
        if msg_size == 0:
            return ""

        msg_str = ''
        nleft = msg_size
        while nleft:
            data = client.recv(nleft)
            if data == '':
                break
            msg_str += data
            nleft -= len(data)

        # Check we got full message
        if nleft == self.header_size and data == '':
            print("MockServer: Could not recv message because socket was closed from client")
            return None
        elif nleft:
            print("MockServer: Got {} of {} expected bytes for header".format(nleft, self.header_size))
            return None

        return msg_str
