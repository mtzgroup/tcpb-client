/** \file tcpb.h
 *  \brief Definition of TCPBClient class
 *  \author Stefan Seritan <sseritan@stanford.edu>
 *  \date Jul 2017
 */

#ifndef TCPB_H_
#define TCPB_H_

#include <string>

#include "terachem_server.pb.h"

// Handles communicating with a TeraChem server through sockets and protocol buffers
// Based on protobufserver.cpp/.h in the TeraChem source code and the Python tcpb (that came first)
// One major difference is that I do not need to use select logic on the sockets (also simplifies threading)
// This is since we are only talking to ONE server
class TCPBClient {
  public:
    //Constructor/Destructor
    TCPBClient(int port);
    ~TCPBClient();

    // Job Settings

    // Server Communication

    // Convenience Functions

  private:
    int port_;
    int server_;
    FILE* clientLogFile_;

    // Socket helper functions
    // These first two are higher level, have error checking and will clean up broken connections
    bool HandleRecv(char* buf, int len, const char* log);
    bool HandleSend(const char* buf, int len, const char* log);
    // These next two are low level, have no error checking built in
    int RecvN(char* buf, int len);
    int SendN(const char* buf, int len);
    // Wrapper for shutdown & close 
    void CloseSock();

    void VerboseLog(const char* format, ...);
}

#endif
