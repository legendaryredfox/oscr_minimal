CXX ?= g++
CXXFLAGS ?= -std=c++11 -Wall -Wextra -O1
CARTS = oscr_carts.cpp oscr_carts_snes.cpp oscr_carts_nes.cpp oscr_carts_md.cpp oscr_carts_gba.cpp oscr_carts_gb.cpp

test: build/test_proto build/test_carts build/test_si5351 build/test_avr_hal
	./build/test_proto
	./build/test_si5351
	./build/test_avr_hal
	./build/test_carts

build/test_avr_hal: tests/test_avr_hal.cpp oscr_avr_buses.h oscr_bus.h oscr_si5351.h tests/avr_mock/Arduino.h tests/avr_mock/Wire.h tests/avr_mock/util/delay.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) -Itests/avr_mock -o $@ tests/test_avr_hal.cpp

build/test_si5351: tests/test_si5351.cpp oscr_si5351.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ tests/test_si5351.cpp

build/test_carts: tests/test_carts.cpp $(CARTS) oscr_session.cpp oscr_proto.cpp oscr_carts.h oscr_bus.h oscr_session.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ tests/test_carts.cpp $(CARTS) oscr_session.cpp oscr_proto.cpp

build/test_proto: tests/test_proto.cpp oscr_proto.cpp oscr_session.cpp oscr_proto.h oscr_session.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ tests/test_proto.cpp oscr_proto.cpp oscr_session.cpp

build/sim_stdio: tests/sim_stdio.cpp oscr_proto.cpp oscr_session.cpp oscr_proto.h oscr_session.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ tests/sim_stdio.cpp oscr_proto.cpp oscr_session.cpp

clean:
	rm -rf build
