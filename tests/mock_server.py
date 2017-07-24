#!/usr/bin/env python
# mock_server.py
# Written by Stefan Seritan on July 16th, 2017
#
# A mock server for TCPB client testing
# Communication is really over sockets, but responses are feed into the mock server beforehand

import numpy as np
import socket
import struct


class MockServer(object):
    """Mock server for TCPB client testing

    Intended testing workflow:
    - Response state of MockServer is set
    - Client call is executed and communicated to mock server over socket
    - Response is sent back to client over socket
    - Output of client function is tested for correctness
    """
    def __init__(self, port):
        """Initialize the MockServer object.

        Args:
            port: Integer of port number
        """
        # Sanity checks
        if not isinstance(port, int):
            raise TypeError("Port number must be an integer")
        if port < 1023:
            raise ValueError("Port number is not allowed to below 1023 (system reserved ports)")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', port))
        self.sock.listen()

        # Expected message from client (passed in unserialized)
        self.expected_header = None
        self.expected_pb = None
        self.got_expected = False

        # Response message for client (passed in unserialized)
        self.response_header = None
        self.response_pb = None

    def set_expected_msg(self, msgType, msgPB):
        

    def set_response_msg(self, msgType, msgPB):
        """Set the response for the mock server

        Args:
            msgType: Integer type of Protocol Buffer
            msgPB: Response Protocol Buffer
        """
        # TODO: Look up actual 
        self.response_header = struct.pack('>II', msgType, msgPB.byteSize())
        self.response_msg = msgPB.ToString()
