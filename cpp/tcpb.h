/** \file tcpb.h
 *  \brief Definition of TCPBClient class
 *  \author Stefan Seritan <sseritan@stanford.edu>
 *  \date Jul 2017
 */

#ifndef TCPB_H_
#define TCPB_H_

#include <string>

#include "terachem_server.pb.h"

#ifndef MAX_STR_LEN
#define MAX_STR_LEN 1024
#endif

/**
 * \brief TeraChem Protocol Buffer (TCPB) Client class
 * Handles communicating with a TeraChem server through sockets and protocol buffers
 * Based on protobufserver.cpp/.h in the TeraChem source code and tcpb.py (that came first)
 * Direct control of the asynchronous server communication is possible,
 * but the typical use would be the convenience functions like ComputeEnergy()
 *
 * One major difference to the TCPB server code is that the client only needs one active connection
 * This removes most threading and select logic (but limits communication to one server)
 * However, timeouts do need to be explicitly set on the socket
 **/
class TCPBClient {
  public:
    //Constructor/Destructor
    TCPBClient(const char* host, int port);
    ~TCPBClient();

    // Job Settings
    void SetJobInput(); //STUB

    /************************
     * SERVER COMMUNICATION *
     ************************/
    /**
     * Checks whether the server is available (does not reserve server)
     *
     * @return True if server has no running job, False otherwise
     **/
    bool IsAvailable(); //STUB

    bool SendJobAsync(); //STUB
    bool CheckJobAsync(); //STUB
    bool RecvJobAsync(); //STUB

    // Convenience Functions
    void ComputeJobSync(); //STUB
    void ComputeEnergy(double& energy); //STUB
    void ComputeGradient(double& energy, double* gradient); //STUB

  private:
    char host[MAX_STR_LEN];
    int port_;
    int server_;
    FILE* clientLogFile_;
    // Protocol buffer variables
    terachem_server::JobInput jobInput_;
    terachem_server::Mol mol_;
    terachem_server::JobOutput jobOutput_;

    /***************************
     * SOCKET HELPER FUNCTIONS *
     ***************************/
    // TODO: These should probably be split out, pretty independent
    // TODO: These functions will not work on Windows at the moment

    /**
     * Initialize the server_ socket and connect to the given host (host_) and port (port_)
     **/
    void Connect();

    /**
     * Disconnect and discard the server_ socket
     **/
    void Disconnect();

    /**
     * A high-level socket recv with error checking and clean up for broken connections
     *
     * @param buf Buffer for incoming packet
     * @param len Byte size of incoming packet
     * @param log String message to be printed out as part of SocketLog messages (easier debugging)
     * @return status True if recv'd full packet, False otherwise (indicating server_ socket is now closed)
     **/
    bool HandleRecv(char* buf, int len, const char* log);

    /**
     * A high-level socket send with error checking and clean up for broken connections
     *
     * @param buf Buffer for outgoing packet
     * @param len Byte size of outgoing packet
     * @param log String message to be printed out as part of SocketLog messages (easier debugging)
     * @return status True if sent full packet, False otherwise (indicating server_ socket is now closed)
     **/
    bool HandleSend(const char* buf, int len, const char* log);

    /**
     * A low-level socket recv wrapper to ensure full packet recv
     *
     * @param buf Buffer for incoming packet
     * @param len Byte size of incoming packet
     * @return nsent Number of bytes recv'd
     **/
    int RecvN(char* buf, int len);

    /**
     * A low-level socket send wrapper to ensure full packet send
     *
     * @param buf Buffer for outgoing packet
     * @param len Byte size of outgoing packet
     * @return nsent Number of bytes sent
     **/
    int SendN(const char* buf, int len);

    /**
     * Verbose logging with timestamps for the client socket into "client.log"
     * This function is similar to fprintf(clientLogFile_, format, ...) with SOCKETLOGS defined
     * This function does nothing without SOCKETLOGS defined
     *
     * @param format Format string for vfprintf
     * @param va_args Variable arguments for vfprintf
     **/
    void SocketLog(const char* format, ...);
}

#endif
