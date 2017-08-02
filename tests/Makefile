CXX=g++
CXXFLAGS=
LIBS=-lprotobuf -ltcpb

.PHONY: all
all: available_test

available_test: available/available_test.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LIBS)
	@mv $@ available/

.PHONY: clean
clean:
	@rm available/available_test
	@rm client.log
