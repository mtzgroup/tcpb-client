#!/usr/bin/env python
# pbhelper.py
# Written by Stefan Seritan on July 28th, 2017
#
# Protobuf helper functions for testing

from . import terachem_server_pb2 as pb

def save_pb(msgType, msgPB, outfile="pb.dat", append=False):
    """Save a Protocol Buffer message (with header) to file
    
    Args:
        msgType: Message type (defined as enum in protocol buffer)
        msgPB: Protocol Buffer to save (if None, only write msgType (used for empty Status messages))
        outfile: File to save the protocol buffer (1 line per message, space separated)
        append: If True, append to outfile. If False, overwrite outfile.
    """
    if append:
        mode = "a"
    else:
        mode = "w"
    with f as open(outfile, mode):
        if msgPB is None:
            f.write("{}\n".format(msgType))
        else:
            f.write("{} {}\n".format(msgType, msgPB.SerializeToString()))
            

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
