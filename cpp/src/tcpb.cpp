/** \file tcpb.cpp
 *  \brief Implementation of TCPBClient class
 *  \author Stefan Seritan <sseritan@stanford.edu>
 *  \date Jul 2017
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string>
#include <time.h>
#include <stdarg.h>

//Socket includes
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/time.h>

#include "tcpb.h"
#include "terachem_server.pb.h"

using namespace std;

// SOCKETLOGS gives the option to turn on detailed socket communication information
// Logs will be written to clientLogFile_, which is usually opened as client.log
#define SOCKETLOGS

TCPBClient::TCPBClient(const char* host, int port) {
  snprintf(host_, MAX_STR_LEN, "%s", host);
  port_ = port;
  server_ = -1;

#ifdef SOCKETLOGS
  clientLogFile_ = fopen("client.log", "w");
#endif
}

TCPBClient::~TCPBClient() {
  Disconnect();

#ifdef SOCKETLOGS
  fclose(clientLogFile_);
#endif
}

/************************
 * SERVER COMMUNICATION *
 ************************/

bool TCPBClient::IsAvailable() {
  uint32_t header[2];
  bool sendSuccess, recvSuccess;

  // Send status request
  header[0] = htonl((uint32_t)terachem_server::STATUS);
  header[1] = htonl((uint32_t)0);
  sendSuccess = HandleSend((char *)header, sizeof(header), "IsAvailable() status header");
  if (!sendSuccess) {
    printf("Could not send status header");
    exit(1);
  }
  
  // Receive status response
  recvSuccess = HandleRecv((char *)header, sizeof(header), "IsAvailable() status header");
  if (!recvSuccess) {
    printf("Could not receive status header");
    exit(1);
  }

  int msgType = ntohl(header[0]);
  int msgSize = ntohl(header[1]);

  char msg[msgSize];
  recvSuccess = HandleRecv(msg, sizeof(msg), "IsAvailable() status protobuf");
  if (!recvSuccess) {
    printf("Could not receive status protobuf");
    exit(1);
  }

  if (header[0] != terachem_server::STATUS) {
    printf("Did not receive the expected status message");
    exit(1);
  }
  
  terachem_server::Status status;
  status.ParseFromString(msg);

  return !status.busy();
}

/***************************
 * SOCKET HELPER FUNCTIONS *
 ***************************/

void TCPBClient::Connect() {
  struct hostent* serverinfo;
  struct sockaddr_in serveraddr;
  struct timeval tv;

  server_ = socket(AF_INET, SOCK_STREAM, 0);

  // Set timeout to 15 seconds
  memset(&tv, 0, sizeof(timeval));
  tv.tv_sec = 15;
  if (setsockopt(server_, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) < 0) {
    SocketLog("Could not set recv timeout to %d seconds", tv.tv_sec);
    exit(1);
  }
  if (setsockopt(server_, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv)) < 0) {
    SocketLog("Could not set send timeout to %d seconds", tv.tv_sec);
    exit(1);
  }

  // Set up connection
  serverinfo = gethostbyname(host_);
  if (serverinfo == NULL) {
    SocketLog("Could not lookup hostname %s", host_);
    exit(1);
  }
  memset(&serveraddr, 0, sizeof(serveraddr));
  serveraddr.sin_family = AF_INET;
  memcpy((char *)&serveraddr.sin_addr.s_addr, (char *)serverinfo->h_addr, serverinfo->h_length);
  serveraddr.sin_port = htons(port_);

  // Connect
  if (connect(server_, (struct sockaddr*)&serveraddr, sizeof(serveraddr)) < 0) {
    SocketLog("Could not connect to host %s, port %d on socket %d", host_, port_, server_);
    exit(1);
  }
}

void TCPBClient::Disconnect() {
  shutdown(server_, SHUT_RDWR);
  close(server_);
  server_ = -1;
}


bool TCPBClient::HandleRecv(char* buf, int len, const char* log) {
  int nrecv;

  // Try to recv
  nrecv = RecvN(buf, len);
  if (nrecv < 0) {
    if (errno == EINTR || errno == EAGAIN) {
      SocketLog("Packet read for %s on socket %d was interrupted, trying again\n", log, server_);
      nrecv = RecvN(buf, len);
    }
  }

  if (nrecv < 0) {
    SocketLog("Could not properly recv packet for %s on socket %d, closing socket. Errno: %d (%s)\n", log, server_, errno, strerror(errno));
    Disconnect();
    return false;
  } else if (nrecv == 0) {
    SocketLog("Received shutdown signal for %s on socket %d, closing socket\n", log, server_);
    Disconnect();
    return false;
  } else if (nrecv != len) {
    SocketLog("Only recv'd %d bytes of %d expected bytes for %s on socket %d, closing socket\n", nrecv, len, log, server_);
    Disconnect();
    return false;
  }
  
  SocketLog("Successfully recv'd packet of %d bytes for %s on socket %d\n", nrecv, log, server_);
  return true;
}

bool TCPBClient::HandleSend(const char* buf, int len, const char* log) {
  int nsent;

  if (len == 0) {
    SocketLog("Trying to send packet of 0 length for %s on socket %d, skipping send\n", log, server_);
    return true;
  }

  // Try to send
  nsent = SendN(buf, len);
  if (nsent < 0) {
    if (errno == EINTR || errno == EAGAIN) {
      SocketLog("Packet send for %s on socket %d was interrupted, trying again\n", log, server_);
      nsent = SendN(buf, len);
    }
  }

  if (nsent <= 0) {
    SocketLog("Could not properly send packet for %s on socket %d, closing socket. Errno: %d (%s)\n", log, server_, errno, strerror(errno));
    Disconnect();
    return false;
  } else if (nsent != len) {
    SocketLog("Only sent %d bytes of %d expected bytes for %s on socket %d, closing socket\n", nsent, len, log, server_);
    Disconnect();
    return false;
  }
  
  SocketLog("Successfully sent packet of %d bytes for %s on socket %d\n", nsent, log, server_);
  return true;
}

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

void TCPBClient::SocketLog(const char* format, ...) {
#ifdef SOCKETLOGS
  // Get time info
  time_t now = time(NULL);
  struct tm* t = localtime(&now);

  // Get full log string from variable arguments
  va_list args;
  va_start(args, format);
  char logStr[MAX_STR_LEN];
  vsnprintf(logStr, MAX_STR_LEN, format, args);

  // Print to file with timestamp
  fprintf(clientLogFile_, "%s: %s\n", asctime(t), logStr);
  fflush(clientLogFile_);

  va_end(args);
#endif
}
