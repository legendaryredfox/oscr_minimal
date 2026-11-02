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
  virtual void write_word(uint32_t word_addr, uint16_t w) = 0;   // escrita em ROM/SRAM (/CE0 + /LWR), como writeWord_MD do OSCR
  virtual void map_write(uint32_t word_addr, uint16_t w) = 0;    // registradores em $A130xx (/TIME + /LWR), como writeSSF2Map
  // EEPROM serial (I2C) de alguns cartuchos. Primitivas do OSCR; a lógica I2C fica em oscr_carts.cpp.
  virtual void eep_enable(bool on) = 0;                                          // EepromInit (Acclaim tipo 2): liga/desliga a EEPROM
  virtual void eep_sda(uint32_t word_addr, uint8_t d, bool slow) = 0;            // writeWord_SDA: D0 vai ao SDA (só /LWR)
  virtual void eep_scl(uint32_t word_addr, uint8_t d, bool slow) = 0;            // writeWord_SCL: D0 vai ao SCL (só /UWR)
  virtual void eep_cm(uint32_t word_addr, uint16_t w) = 0;                       // writeWord_CM (Codemasters): /UWR + pulsos de clock
};

struct GbaBus {  // AD0..15 multiplexado (PF/PK), A16..A23 em PC
  virtual ~GbaBus() {}
  virtual void begin() = 0;
  virtual void end() = 0;
  virtual uint16_t word(uint32_t byte_addr) = 0;  // endereço em bytes (par)
  virtual uint8_t sram_read(uint16_t addr) = 0;   // SRAM (/CS2): endereço em AD0-15, dado em D0-D7
  virtual void sram_write(uint16_t addr, uint8_t value) = 0;
  // EEPROM serial pelo barramento da ROM (A23 alto, bit a bit): lê o bloco de 8 bytes de índice `block`.
  // big = false: 4 Kbit (512 bytes, endereço de 6 bits); true: 64 Kbit (8 KB, endereço de 14 bits).
  virtual void eeprom_block(uint16_t block, bool big, uint8_t out[8]) = 0;
};

}  // namespace oscr
