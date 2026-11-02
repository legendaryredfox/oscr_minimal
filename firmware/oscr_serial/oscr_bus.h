// SPDX-License-Identifier: GPL-3.0-or-later
// Interfaces de barramento dos cartuchos. A implementação para o Mega está em oscr_avr_buses.h
// (sequências de porta copiadas do OSCR); os testes usam cartuchos simulados.
#pragma once
#include <stdint.h>

namespace oscr {

struct SnesBus {  // 24 bits: banco (PL) + endereço (PF/PK), dado em PC
  virtual ~SnesBus() {}
  virtual void begin() = 0;
  virtual void end() = 0;
  virtual uint8_t read(uint8_t bank, uint16_t addr) = 0;
  virtual void write(uint8_t bank, uint16_t addr, uint8_t value) = 0;
};

struct NesBus {  // NES e Famicom: mesmo barramento
  virtual ~NesBus() {}
  virtual void begin() = 0;
  virtual void end() = 0;
  virtual uint8_t prg(uint16_t addr) = 0;  // CPU $0000-$FFFF (ROM em $8000-$FFFF)
  virtual uint8_t chr(uint16_t addr) = 0;  // PPU $0000-$1FFF
  virtual void prg_write(uint16_t addr, uint8_t value) = 0;  // escrita de registrador do mapper ($8000-$FFFF)
};

struct MdBus {  // dados de 16 bits (PA = D8..D15, PC = D0..D7)
  virtual ~MdBus() {}
  virtual void begin() = 0;
  virtual void end() = 0;
  virtual uint16_t word(uint32_t word_addr) = 0;  // endereço em palavras (byte >> 1)
};

struct GbaBus {  // AD0..15 multiplexado (PF/PK), A16..A23 em PC
  virtual ~GbaBus() {}
  virtual void begin() = 0;
  virtual void end() = 0;
  virtual uint16_t word(uint32_t byte_addr) = 0;  // endereço em bytes (par)
};

}  // namespace oscr
