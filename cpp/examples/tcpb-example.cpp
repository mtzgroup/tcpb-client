/** \file tcpb-example.cpp
 *  \brief Example of TCPBClient use
 *  \author Stefan Seritan <sseritan@stanford.edu>
 *  \date Aug 2017
 */

#include <stdio.h>
#include <stdlib.h>
#include <string>

#include "tcpb.h"

int main(int argc, char** argv) {
  if (argc != 3) {
    printf("Usage: %s host port\n", argv[0]);
  }

  int port = atoi(argv[2]);
  TCPBClient* TC = new TCPBClient(argv[1], port);

  TC->Connect();

  bool avail = TC->IsAvailable();
  printf("Server is available: %s\n", (avail ? "True" : "False"));

  // Memory Management
  delete TC; //Handles disconnect

  return 0;
}
