# Testes de PC do port do CIC. Requer gputils (gpasm) e g++.
#   make test      monta lock e key com o gpasm, confere o lock contra o .hex oficial e roda a simulação
BUILD := build
TP    := ../third_party

all: test

$(BUILD):
	mkdir -p $(BUILD)

# O key do sd2snes termina com uma seção "DEEPROM CODE" que o gpasm só aceita em modo de objeto;
# o patch troca por "org 0x2100" (endereço da EEPROM de dados no .hex).
$(BUILD)/key.asm: $(TP)/snescic-key.asm | $(BUILD)
	sed -e 's/^DEEPROM\tCODE/\torg 0x2100/' -e 's/^end$$/\tend/' $< > $@

$(BUILD)/key.hex: $(BUILD)/key.asm
	cd $(BUILD) && gpasm -p p12f629 -q -o key.hex key.asm

$(BUILD)/lock.hex: $(TP)/snescic-lock-resync.asm | $(BUILD)
	cd $(BUILD) && gpasm -p p12f629 -q -o lock.hex ../$<

$(BUILD)/sim: sim.cpp ../cic_rp2040/pic12f629.h | $(BUILD)
	g++ -std=c++17 -O2 -Wall -Wextra -o $@ sim.cpp

# O .hex montado tem que ser igual ao distribuído pelo sd2snes.
check-hex: $(BUILD)/lock.hex
	diff <(tr -d '\r' < $(BUILD)/lock.hex) <(tr -d '\r' < $(TP)/snescic-lock-resync.hex)
	@echo "lock.hex montado == snescic-lock-resync.hex do sd2snes"

test: check-hex $(BUILD)/sim $(BUILD)/key.hex
	$(BUILD)/sim $(BUILD)/lock.hex $(BUILD)/key.hex 9
	$(BUILD)/sim $(BUILD)/lock.hex $(BUILD)/key.hex 6

clean:
	rm -rf $(BUILD)

.PHONY: all test check-hex clean
SHELL := /bin/bash
