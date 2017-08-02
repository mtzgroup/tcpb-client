CXX=g++
INCDIR=./include
CXXFLAGS=-I$(INCDIR) -fPIC
VER=0.1.0

# Source files
SRCDIR=./src
_SRC=tcpb.cpp terachem_server.pb.cpp
SRC=$(patsubst %,$(SRCDIR)/%,$(_SRC))

# Header files (based on source filenames)
_DEPS=$(_SRC:.cpp=.h)
DEPS=$(patsubst %,$(INCDIR)/%,$(_DEPS))

# Object files (also based on source filenames)
OBJDIR=./obj
_OBJ=$(_SRC:.cpp=.o)
OBJ=$(patsubst %,$(OBJDIR)/%,$(_OBJ))

# Library flags
LIBS=-lprotobuf


# Rule to build object files in obj/
# TODO: This recompiles all object files if any header changes, not ideal
$(OBJDIR)/%.o: $(SRCDIR)/%.cpp $(DEPS)
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# Rule to build versioned tcpb.so
tcpb.so.$(VER): $(OBJ)
	$(CXX) $(CXXFLAGS) -shared -o $@ $^ $(LIBS)
	@ln -s $@ tcpb.so

.PHONY: clean

clean:
	rm -r $(OBJDIR)/*.o tcpb.so tcpb.so.*
