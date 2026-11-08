# Testes do protocolo no PC (sem AVR, sem cartucho): framing, CRC32, sessão (modo MOCK e modo fluxo).
# Usa os arquivos do próprio fork (../src/dumper), os mesmos que vão para o Mega.
CXX ?= g++
CXXFLAGS ?= -std=c++11 -Wall -Wextra -O1
SRC = ../src/dumper/oscr_proto.cpp ../src/dumper/oscr_session.cpp
HDR = ../src/dumper/oscr_proto.h ../src/dumper/oscr_session.h

test: build/test_proto build/test_snes_plan build/test_mdflash build/test_power_core build/test_sms
	./build/test_power_core
	./build/test_sms
	./build/test_proto
	./build/test_snes_plan
	./build/test_mdflash

build/test_power_core: test_power_core.cpp ../include/dumper/PowerCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_power_core.cpp

build/test_sms: test_sms.cpp ../include/dumper/SmsCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_sms.cpp

build/test_mdflash: test_mdflash.cpp md_chip_model.h ../include/dumper/MdFlashCore.h
	mkdir -p build
	$(CXX) -std=c++17 -Wall -Wextra -O1 -o $@ test_mdflash.cpp

build/test_snes_plan: test_snes_plan.cpp ../include/dumper/SnesPlan.h
	mkdir -p build
	$(CXX) -std=c++17 -Wall -Wextra -O1 -o $@ test_snes_plan.cpp

build/test_proto: test_proto.cpp $(SRC) $(HDR)
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ test_proto.cpp $(SRC)

build/sim_stdio: sim_stdio.cpp $(SRC) $(HDR)
	mkdir -p build
	$(CXX) $(CXXFLAGS) -o $@ sim_stdio.cpp $(SRC)

clean:
	rm -rf build
