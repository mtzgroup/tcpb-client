CXX=g++
PROTOC=protoc
INCDIR=./include
CXXFLAGS=-I$(INCDIR) -fPIC
LIBS=-lprotobuf
VER=0.2.0

# Subdirectories
SRCDIR=./src
OBJDIR=./obj
BUILDDIR=./build
PROTODIR=../proto

# Prefix for installation
PREFIX=/global/user_software/tcpb-client/$(VER)

.PHONY: all
all: $(SRCDIR)/terachem_server.pb.cpp libtcpb.so.$(VER)

# Rule to compile .proto file
$(SRCDIR)/terachem_server.pb.cpp: $(PROTODIR)/terachem_server.proto
	$(PROTOC) $< --proto_path=$(PROTODIR) --cpp_out=.
	@mv terachem_server.pb.cc $(SRCDIR)/terachem_server.pb.cpp
	@mv terachem_server.pb.h $(INCDIR)

# Rule to build object files in obj/
$(OBJDIR)/terachem_server.pb.o: $(SRCDIR)/terachem_server.pb.cpp $(INCDIR)/terachem_server.pb.h
	@mkdir -p $(OBJDIR)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

$(OBJDIR)/tcpb.o: $(SRCDIR)/tcpb.cpp $(INCDIR)/tcpb.h $(INCDIR)/terachem_server.pb.h
	@mkdir -p $(OBJDIR)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# Rule to build versioned tcpb.so
libtcpb.so.$(VER): $(OBJDIR)/tcpb.o $(OBJDIR)/terachem_server.pb.o
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -shared -o $(BUILDDIR)/$@ $^ $(LIBS)

.PHONY: clean
clean:
	@rm -r $(OBJDIR)/*.o $(BUILDDIR)/libtcpb.so.$(VER)
	@rm -r $(SRCDIR)/terachem_server.pb.cpp $(INCDIR)/terachem_server.pb.h

.PHONY: install
install:
	@echo "Installing TCPB C++ client into $(PREFIX)"
	@mkdir -p $(PREFIX)/lib
	@cp -v $(BUILDDIR)/libtcpb.so.$(VER) $(PREFIX)/lib
	@ln -sfn $(PREFIX)/lib/libtcpb.so.$(VER) $(PREFIX)/lib/libtcpb.so
	@mkdir -p $(PREFIX)/include
	@cp -v $(INCDIR)/tcpb.h $(PREFIX)/include
	@cp -v $(INCDIR)/terachem_server.pb.h $(PREFIX)/include

.PHONY: uninstall
uninstall:
	@echo "Uninstalling TCPB C++ client from $(PREFIX)"
	@rm -v $(PREFIX)/lib/{libtcpb.so.$(VER),libtcpb.so}
	@rm -v $(PREFIX)/include/{tcpb.h,terachem_server.pb.h}
