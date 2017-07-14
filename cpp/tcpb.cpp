/** \file tcpb.cpp
 *  \brief Implementation of TCPBClient class
 *  \author Stefan Seritan <sseritan@stanford.edu>
 *  \date Jul 2017
 */

#include <stdio.h>

//Socket includes
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/time.h>

#include "tcpb.h"
#include "terachem_server.pb.h"

using namespace std;

// Similar to TeraChem's protobufserver.cpp, I use VERBOSELOGS to give the option to turn off detailed socket communication information
#define VERBOSELOGS

/*
 * Constructors/Destructors
 */
TCPBClient::TCPBClient(int port) {
  port_ = port;

#ifdef VERBOSELOGS
  clientLogFile_ = fopen("client.log", "w");
#endif
}

TCPBClient::TCPBClient() {
  CloseSock();

#ifdef VERBOSELOGS
  fclose(clientLogFile_);
#endif
}

/*
 * Packet read/write functions from the socket
 */
// Wrapper for RecvN that can clear a bad connection from active connections and can take a string for better output
// Returns true if recv was successful, and false otherwise (signalling socket was closed)
bool TCPBClient::HandleRecv(char* buf, int len, const char* log) {
  int nrecv;

  // Try to recv
  nrecv = RecvN(buf, len);
  if (nrecv < 0) {
    if (errno == EINTR || errno == EAGAIN) {
      VerboseLog("Packet read for %s on socket %d was interrupted, trying again\n", log, server_);
      nrecv = RecvN(buf, len);
    }
  }

  if (nrecv < 0) {
    VerboseLog("Could not properly recv packet for %s on socket %d, closing socket. Errno: %d (%s)\n", log, server_, errno, strerror(errno));
    CloseSock();
    return false;
  } else if (nrecv == 0) {
    VerboseLog("Received shutdown signal for %s on socket %d, closing socket\n", log, server_);
    CloseSock();
    return false;
  } else if (nrecv != len) {
    VerboseLog("Only recv'd %d bytes of %d expected bytes for %s on socket %d, closing socket\n", nrecv, len, log, server_);
    CloseSock();
    return false;
  }
  
  VerboseLog("Successfully recv'd packet of %d bytes for %s on socket %d\n", nrecv, log, server_);
  return true;
}

// Wrapper for SendN that can clear a bad connection from active connections and can take a string for better output
// Returns true if send was successful, and false otherwise (signalling socket was closed)
bool TCPBClient::HandleSend(const char* buf, int len, const char* log) {
  int nsent;

  if (len == 0) {
    VerboseLog("Trying to send packet of 0 length for %s on socket %d, skipping send\n", log, server_);
    return true;
  }

  // Try to send
  nsent = SendN(buf, len);
  if (nsent < 0) {
    if (errno == EINTR || errno == EAGAIN) {
      VerboseLog("Packet send for %s on socket %d was interrupted, trying again\n", log, server_);
      nsent = SendN(buf, len);
    }
  }

  if (nsent <= 0) {
    VerboseLog("Could not properly send packet for %s on socket %d, closing socket. Errno: %d (%s)\n", log, server_, errno, strerror(errno));
    CloseSock();
    return false;
  } else if (nsent != len) {
    VerboseLog("Only sent %d bytes of %d expected bytes for %s on socket %d, closing socket\n", nsent, len, log, server_);
    CloseSock();
    return false;
  }
  
  VerboseLog(logStr_, "Successfully sent packet of %d bytes for %s on socket %d\n", nsent, log, server_);
  return true;
}
// RecvN and SendN are just to make sure we recv/send the full buffer, since we are not guaranteed it will go in one shot over TCP
int TCPBClient::RecvN(char* buf, int len) {
  int nleft, nrecv;

  nleft = len;
  while (nleft) {
    nrecv = recv(server_, buf, len, 0);
    if (nrecv < 0) return nrecv;
    else if (nrecv == 0) break;

    nleft -= nrecv; 
    buf += nrecv;
  }

  return len - nleft;
}

int TCPBClient::SendN(const char* buf, int len) {
  int nleft, nsent;

  nleft = len;
  while (nleft) {
    nsent = send(server_, buf, len, 0);
    if (nsent < 0) return nsent;
    else if (nsent == 0) break;

    nleft -= nsent; 
    buf += nsent;
  }

  return len - nleft;
}

// Close socket
void TCPBClient::CloseSock() {
    shutdown(server, SHUT_RDWR);
    close(server);
    server_ = -1;
}

// Log formatted error message to client file, includes timestamp and newline
// I'm using vargs to make the function nice to call, which is clever (aka bad) but better than a macro (imo)
void TCPBClient::VerboseLog(const char* format, ...) {
#ifdef VERBOSELOGS
  // Get time info
  time_t now = time(NULL);
  struct tm* t = localtime(&now);

  // Get full log string from variable arguments
  va_list args;
  va_start(args, format);
  char logStr[1024];
  snprintf(logStr, 1024, format, args);

  // Print to file with timestamp
  vfprintf(clientLogFile_, "%s: %s\n", asctime(t), logStr);
  fflush(clientLogFile_);

  va_end(args);
#endif
}
