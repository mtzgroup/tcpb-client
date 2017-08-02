CXX=g++
INCDIR=./include
CXXFLAGS=-I$(INCDIR) -fPIC
LIBS=-lprotobuf
VER=0.1.0

# Source files
SRCDIR=./src
_SRC=tcpb.cpp terachem_server.pb.cpp

# Header files (based on source filenames)
_DEPS=$(_SRC:.cpp=.h)
DEPS=$(patsubst %,$(INCDIR)/%,$(_DEPS))

# Object files (also based on source filenames)
OBJDIR=./obj
_OBJ=$(_SRC:.cpp=.o)
OBJ=$(patsubst %,$(OBJDIR)/%,$(_OBJ))

# Build directory
BUILDDIR=./build

# Prefix for installation
PREFIX=/home/sseritan/personal_modules/software/tcpb-client/0.1


# Rule to build object files in obj/
# TODO: This recompiles all object files if any header changes, not ideal
$(OBJDIR)/%.o: $(SRCDIR)/%.cpp $(DEPS)
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# Rule to build versioned tcpb.so
libtcpb.so.$(VER): $(OBJ)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -shared -o $(BUILDDIR)/$@ $^ $(LIBS)

.PHONY: clean
clean:
	rm -r $(OBJDIR)/*.o $(BUILDDIR)/libtcpb.so.$(VER)


.PHONY: install
install:
	@echo "Installing libtpcb.so into $(PREFIX)/lib"
	@mkdir -p $(PREFIX)/lib
	@cp $(BUILDDIR)/libtcpb.so.$(VER) $(PREFIX)/lib
	@ln -sfn $(PREFIX)/lib/libtcpb.so.$(VER) $(PREFIX)/lib/libtcpb.so

.PHONY: uninstall
uninstall:
	@echo "Uninstalling libtcpb.so from $(PREFIX)/lib"
	@rm $(PREFIX)/lib/libtcpb.so $(PREFIX)/lib/libtcpb.so.$(VER)
