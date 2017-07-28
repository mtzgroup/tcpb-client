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


class MockServer(object):
    """Mock server for TCPB client testing

    Intended testing workflow:
    - Response state of MockServer is set
    - Client call is executed and communicated to mock server over socket
    - Response is sent back to client over socket (on listening thread)
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

        self.headerSize = 8 #Expect exactly 2 ints of 4 bytes each
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('localhost', port))
        self.activeListening = True
        self.clientThreads = []

        # Expected messages from client
        # Passed as (msgType, msgPB)
        self.expected_queue = Queue()

        # Response message for client
        # Passed as (msgType, msgPB)
        self.response_queue = Queue()

    def add_expected_messages(self, msgs):
        """Add messages to the expected messages queue

        Args:
            msgs: List of (msgType, msgPB) tuples
        """
        for m in msgs:
            self.expected_queue.put(m)

    def add_response_messages(self, msgs):
        """Add messages to the response messages queue

        Args:
            msgs: List of (msgType, msgPB) tuples
        """
        for m in msgs:
            self.response_queue.put(m)

    def set_response_msg(self, msgType, msgPB):
        """Set the response for the mock server

        Args:
            msgType: Integer type of Protocol Buffer
            msgPB: Response Protocol Buffer
        """
        # TODO: Look up actual 
        self.response_header = struct.pack('>II', msgType, msgPB.byteSize())
        self.response_msg = msgPB.ToString()

    def listen(self):
        self.sock.listen(5)
        while self.activeListening:
            client, address = self.sock.accept()
            client.settimeout(60)
            t = Thread(target=self.testClient, args=(client, address))
            t.start()
            self.clientThreads += [t]

    def testClient(self, client, address):    
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
            msgStr = self._recv_message(client, header[1])
        except socket.error as msg:
            raise RuntimeError("MockServer: Problem receiving message from client. Error: {}".format(msg))

        # TODO: Test protobuf is the same

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
        self.activeListening = False
        for t in self.clientThreads:
            t.join()

    # Private send/recv functions
    def _send_header(self, client, msgType, msgSize):
        """Sends a header to the TCPBClient

        Args:
            client: Client socket
            msgSize: Size of following message (not including header)
            msgType: Message type (defined as enum in protocol buffer)
        Returns True if send was successful, False otherwise
        """
        # This will always pack integers as 4 bytes since I am requesting a standard packing (big endian)
        # Big endian is convention for network byte order (because IBM or someone)
        header = struct.pack('>II', msgType, msgSize)
        try:
            client.sendall(header)
        except socket.error as msg:
            print("MockServer: Could not send header. Error: {}".format(msg))
            return False

        return True

    def _send_message(self, client, msgStr):
        """Sends a header to the TCPBClient

        Args:
            client: Client socket
            msgStr: String representation of binary message
        Returns True if send was successful, False otherwise
        """
        try:
            client.sendall(msgStr)
        except socket.error as msg:
            print("MockServer: Could not send message. Error: {}".format(msg))
            return False

        return True

    def _recv_header(self, client):
        """Receive a header from the TCPBClient

        Args:
            client: Client socket
        Returns (msgType, msgSize) on successful recv, None otherwise
        """
        headerStr = ''
        nleft = self.headerSize
        while nleft:
            data = client.recv(nleft)
            if data == '':
                break
            headerStr += data
            nleft -= len(data)

        # Check we got full message
        if nleft == self.headerSize and data == '':
            print("MockServer: Could not recv header because socket was closed from client")
            return None
        elif nleft:
            print("MockServer: Got {} of {} expected bytes for header".format(nleft, self.headerSize)
            return None

        msgInfo = struct.unpack_from(">II", headerStr)
        return msgInfo

    def _recv_message(self, client, msgSize):
        """Receive a message from the TCPBClient

        Args:
            client: Client socket
            msgSize: Integer of message size
        Returns a string representation of the binary message if successful, None otherwise
        """
        if msgSize == 0:
            return ""

        msgStr = ''
        nleft = msgSize
        while nleft:
            data = client.recv(nleft)
            if data == '':
                break
            msgStr += data
            nleft -= len(data)

        # Check we got full message
        if nleft == self.headerSize and data == '':
            print("MockServer: Could not recv message because socket was closed from client")
            return None
        elif nleft:
            print("MockServer: Got {} of {} expected bytes for header".format(nleft, self.headerSize))
            return None

        return msgStr
