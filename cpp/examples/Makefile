CXX=g++
INCDIR=../include
CXXFLAGS=-I$(INCDIR)

# Library flags
LIBS=-lprotobuf -ltcpb

tcpb-example: tcpb-example.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LIBS)

.PHONY: clean
clean:
	@rm -rv tcpb-example client.log
