CXX ?= g++
CXXFLAGS ?= -std=c++11 -Wall -Wextra -O1

test: build/test_proto
	./build/test_proto

build/test_proto: tests/test_proto.cpp oscr_proto.cpp oscr_session.cpp oscr_proto.h oscr_session.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ tests/test_proto.cpp oscr_proto.cpp oscr_session.cpp

build/sim_stdio: tests/sim_stdio.cpp oscr_proto.cpp oscr_session.cpp oscr_proto.h oscr_session.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ tests/sim_stdio.cpp oscr_proto.cpp oscr_session.cpp

clean:
	rm -rf build
