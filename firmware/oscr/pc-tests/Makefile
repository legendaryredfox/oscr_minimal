# Testes do protocolo no PC (sem AVR, sem cartucho): framing, CRC32, sessão (modo MOCK e modo fluxo).
# Usa os arquivos do próprio fork (../src/dumper), os mesmos que vão para o Mega.
CXX ?= g++
CXXFLAGS ?= -std=c++11 -Wall -Wextra -O1
SRC = ../src/dumper/oscr_proto.cpp ../src/dumper/oscr_session.cpp
HDR = ../src/dumper/oscr_proto.h ../src/dumper/oscr_session.h

test: build/test_proto build/test_snes_plan build/test_mdflash build/test_sms build/test_n64 build/test_snes_type build/test_nes build/test_gba369 build/test_snesacc build/test_mdextra build/test_mdbank build/test_gbacc build/test_colv build/test_ngp build/test_vec build/test_arc build/test_rca build/test_pyu build/test_sv build/test_a26
	./build/test_nes
	./build/test_gba369
	./build/test_snesacc
	./build/test_mdextra
	./build/test_mdbank
	./build/test_gbacc
	./build/test_snes_type
	./build/test_sms
	./build/test_colv
	./build/test_ngp
	./build/test_vec
	./build/test_arc
	./build/test_rca
	./build/test_pyu
	./build/test_sv
	./build/test_a26
	./build/test_n64
	./build/test_proto
	./build/test_snes_plan
	./build/test_mdflash

build/test_sms: test_sms.cpp ../include/dumper/SmsCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_sms.cpp

build/test_colv: test_colv.cpp ../include/dumper/ColvCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_colv.cpp

build/test_ngp: test_ngp.cpp ../include/dumper/NgpCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_ngp.cpp

build/test_vec: test_vec.cpp ../include/dumper/VecCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_vec.cpp

build/test_arc: test_arc.cpp ../include/dumper/ArcCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_arc.cpp

build/test_rca: test_rca.cpp ../include/dumper/RcaCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_rca.cpp

build/test_pyu: test_pyu.cpp ../include/dumper/PyuCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_pyu.cpp

build/test_sv: test_sv.cpp ../include/dumper/SvCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_sv.cpp

build/test_a26: test_a26.cpp ../include/dumper/AtariCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_a26.cpp

build/test_snes_type: test_snes_type.cpp ../include/dumper/SnesType.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_snes_type.cpp

build/test_nes: test_nes.cpp ../include/dumper/NesCore.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_nes.cpp

build/test_gba369: test_gba369.cpp ../include/dumper/Gba369.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_gba369.cpp

build/test_snesacc: test_snesacc.cpp ../include/dumper/SnesAcc.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_snesacc.cpp

build/test_gbacc: test_gbacc.cpp ../include/dumper/GbAcc.h ../include/dumper/GbRtc.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_gbacc.cpp

build/test_mdextra: test_mdextra.cpp ../include/dumper/MdExtra.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_mdextra.cpp

build/test_mdbank: test_mdbank.cpp ../include/dumper/MdBank.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_mdbank.cpp

build/test_n64: test_n64.cpp ../include/dumper/N64Core.h
	mkdir -p build
	$(CXX) -std=c++11 -Wall -Wextra -O1 -o $@ test_n64.cpp

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
