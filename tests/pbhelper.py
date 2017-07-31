#!/usr/bin/env python
# pbhelper.py
# Written by Stefan Seritan on July 28th, 2017
#
# Protobuf helper functions for testing

import struct

from . import terachem_server_pb2 as pb

def load_trace(tracefile):
    """Load a packet trace from a TCPB client job run with trace=True
    
    Args:
        tracefile: If True, append to outfile. If False, overwrite outfile.
    Returns:
        msgs: List of (msg_type, msg_pb) from tracefile
    """
    f.open(tracefile, 'rb')
    data = f.read()
    f.close()

    msgs = []
    while len(data) > 0:
        msg_type = struct.unpack_from('>I', data[:4])
        msg_size = struct.unpack_from('>I', data[4:8])
        msg_end = msg_size + 8

        if msg_type == pb.STATUS:
            msg_pb = pb.Status()
        elif msg_type == pb.MOL:
            msg_pb = pb.Mol()
        elif msg_type == pb.JOBINPUT:
            msg_pb = pb.JobInput()
        elif msg_type == pb.JOBOUTPUT:
            msg_pb = pb.JobOutput()
        else:
            raise RuntimeError("PBHelper: Unknown message type {} for received message.".format(msg_type))

        if len(data) < msg_end:
            raise RuntimeError("PBHelper: Ran out of trace.")

        msg_pb.ParseFromString(data[8:msg_end])

        msgs += [(msg_type, msg_pb)]

        del data[:msg_end]

    return msgs

def compare_pb(pb1, pb2):
    """Compare two Protocol Buffers for 'equality'
    For fields in both PBs, they must be equal
    For fields that are in one PB but not the other, they must be empty

    This uses SerializeToString(), but it is important to do this
    locally so that the fields are stored in the same order

    Args:
        pb1: First Protocol Buffer
        pb2: Second Protocol Buffer
    Returns True if equal, False if different
    """
    return pb1.SerializeToString() == pb2.SerializeToString()
