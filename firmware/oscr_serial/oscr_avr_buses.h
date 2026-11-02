// SPDX-License-Identifier: GPL-3.0-or-later
// HAL dos barramentos para o ATmega2560. As sequências de porta/bit vêm do OSCR
// (SNES.ino, NES.ino, MD.ino, GBA.ino, GPL v3) e os pinos conferem com docs/pinmap.md.
// NÃO VALIDADO EM HARDWARE: a lógica acima desta camada é testada no PC (tests/test_carts.cpp).
#pragma once
#if defined(ARDUINO) && defined(__AVR_ATmega2560__)
#include <Arduino.h>
#include <util/delay.h>

#include "oscr_bus.h"

#define OSCR_NOP __asm__ __volatile__("nop\n\t")
#define OSCR_NOP4 do { OSCR_NOP; OSCR_NOP; OSCR_NOP; OSCR_NOP; } while (0)

namespace oscr {

// Deixa os pinos dos slots como entrada, sem pull-up (não mexe em D0/D1 = serial, D38 = LED, SPI).
static inline void bus_release() {
  DDRA = 0; PORTA = 0; DDRC = 0; PORTC = 0; DDRF = 0; PORTF = 0; DDRK = 0; PORTK = 0; DDRL = 0; PORTL = 0;
  const uint8_t h = (1 << 0) | (1 << 1) | (1 << 3) | (1 << 4) | (1 << 5) | (1 << 6);
  DDRH &= ~h; PORTH &= ~h;
  DDRJ &= ~((1 << 0) | (1 << 1)); PORTJ &= ~((1 << 0) | (1 << 1));
  DDRG &= ~(1 << 5); PORTG &= ~(1 << 5);
  DDRE &= ~((1 << 4) | (1 << 5)); PORTE &= ~((1 << 4) | (1 << 5));
}

struct AvrSnesBus : SnesBus {
  void begin() override {
    DDRF = 0xFF; DDRK = 0xFF; DDRL = 0xFF; DDRA = 0xFF;                 // A0-A15, BA0-BA7, PA0-PA7
    DDRH |= (1 << 0) | (1 << 3) | (1 << 5) | (1 << 6) | (1 << 1);       // RST, CS, WR, RD, CLK
    PORTH |= (1 << 0) | (1 << 5);                                       // RST e WR altos
    PORTH &= ~((1 << 3) | (1 << 6) | (1 << 1));                         // CS e RD baixos
    DDRE |= (1 << 5); PORTE &= ~(1 << 5);                               // REFRESH baixo
    DDRH &= ~(1 << 4); DDRG &= ~(1 << 5);                               // IRQ e EXPAND como entrada
    DDRC = 0x00;                                                        // dados como entrada
    delay(20);
  }
  void end() override { bus_release(); }
  uint8_t read(uint8_t bank, uint16_t addr) override {
    PORTL = bank; PORTF = addr & 0xFF; PORTK = addr >> 8;
    OSCR_NOP4; OSCR_NOP; OSCR_NOP;                                      // ~375 ns, como no OSCR
    return PINC;
  }
  void write(uint8_t bank, uint16_t addr, uint8_t v) override {
    PORTH |= (1 << 6) | (1 << 5);                                       // RD e WR altos
    DDRC = 0xFF;
    PORTL = bank; PORTF = addr & 0xFF; PORTK = addr >> 8; PORTC = v;
    OSCR_NOP4; OSCR_NOP4;
    PORTH &= ~(1 << 5);                                                 // WR baixo
    OSCR_NOP4; OSCR_NOP4; OSCR_NOP4; OSCR_NOP4;
    PORTH |= (1 << 5);                                                  // WR alto
    OSCR_NOP4; OSCR_NOP4; OSCR_NOP4; OSCR_NOP4;
    DDRC = 0x00;
    PORTH &= ~(1 << 6);                                                 // RD baixo (leitura)
  }
};

struct AvrNesBus : NesBus {   // NES e Famicom
  static void set_address(uint16_t a) {
    PORTL = a & 0xFF; PORTA = a >> 8;
    if ((a >> 13) & 1) PORTF &= ~(1 << 4); else PORTF |= (1 << 4);      // CHR /A13
  }
  void begin() override {
    DDRF = 0b10110111; PORTF = 0xFF; DDRL = 0xFF; DDRA = 0xFF;
    DDRC &= ~(1 << 2); PORTC |= (1 << 2);                               // CIRAM A10 como entrada
    PORTK = 0xFF; DDRK = 0;
    set_address(0);
    delay(20);
  }
  void end() override { bus_release(); }
  uint8_t prg(uint16_t a) override {
    PORTK = 0xFF; DDRK = 0;                                             // MODE_READ
    PORTF |= (1 << 7);                                                  // PRG_READ
    PORTF |= (1 << 1);                                                  // ROMSEL alto
    set_address(a);
    PORTF |= (1 << 0);                                                  // PHI2 alto
    if (a & 0x8000) PORTF &= ~(1 << 1); else PORTF |= (1 << 1);         // ROMSEL baixo se >= $8000
    _delay_us(1);
    return PINK;
  }
  void prg_write(uint16_t a, uint8_t v) override {                       // write_prg_byte do OSCR
    PORTF &= ~(1 << 0);                                                 // PHI2 baixo
    PORTF |= (1 << 1);                                                  // ROMSEL alto
    DDRK = 0xFF;                                                        // MODE_WRITE
    PORTF &= ~(1 << 7);                                                 // PRG_WRITE
    PORTK = v;
    set_address(a);
    PORTF |= (1 << 0);                                                  // PHI2 alto
    if (a & 0x8000) PORTF &= ~(1 << 1); else PORTF |= (1 << 1);
    _delay_us(1);
    PORTF &= ~(1 << 0);                                                 // PHI2 baixo
    _delay_us(1);
    PORTF |= (1 << 1);                                                  // ROMSEL alto
    PORTF |= (1 << 7);                                                  // PRG_READ
    PORTK = 0xFF; DDRK = 0;                                             // MODE_READ
    set_address(0);
    PORTF |= (1 << 0);
  }
  uint8_t chr(uint16_t a) override {
    PORTK = 0xFF; DDRK = 0;
    PORTF |= (1 << 0);                                                  // PHI2 alto
    PORTF |= (1 << 1);                                                  // ROMSEL alto
    set_address(a);
    PORTF &= ~(1 << 5);                                                 // CHR /RD baixo
    _delay_us(1);
    uint8_t r = PINK;
    PORTF |= (1 << 5);
    return r;
  }
};

struct AvrMdBus : MdBus {
  static void pulse_clock(int n) { for (int i = 0; i < n; i++) PORTH ^= (1 << 1); }
  void begin() override {
    DDRF = 0xFF; DDRK = 0xFF; DDRL = 0xFF;
    DDRH |= (1 << 0) | (1 << 1) | (1 << 3) | (1 << 4) | (1 << 5) | (1 << 6);
    DDRJ |= (1 << 0) | (1 << 1); DDRG |= (1 << 5);
    DDRC = 0x00; DDRA = 0x00;
    PORTH |= (1 << 0) | (1 << 3) | (1 << 4) | (1 << 5) | (1 << 6);
    PORTJ |= (1 << 0) | (1 << 1); PORTG |= (1 << 5);
    delay(200);
  }
  void end() override { bus_release(); }
  uint16_t word(uint32_t a) override {
    PORTF = a & 0xFF; PORTK = (a >> 8) & 0xFF; PORTL = (a >> 16) & 0xFF;
    OSCR_NOP;
    PORTH &= ~(1 << 3); PORTH &= ~(1 << 6); PORTJ &= ~(1 << 1); PORTG &= ~(1 << 5);   // CE0, OE, AS, ASEL
    pulse_clock(10);
    OSCR_NOP4; OSCR_NOP; OSCR_NOP;
    uint16_t w = (uint16_t(PINA) << 8) | PINC;
    PORTH |= (1 << 3); PORTH |= (1 << 6); PORTJ |= (1 << 1); PORTG |= (1 << 5);
    pulse_clock(10);
    OSCR_NOP4;
    return w;
  }
  static void data_out() { DDRC = 0xFF; DDRA = 0xFF; }
  static void data_in() { DDRC = 0x00; DDRA = 0x00; PORTC = 0xFF; PORTA = 0xFF; }
  void write_word(uint32_t a, uint16_t w) override {                    // writeWord_MD do OSCR
    data_out();
    PORTF = a & 0xFF; PORTK = (a >> 8) & 0xFF; PORTL = (a >> 16) & 0xFF;
    PORTC = w & 0xFF; PORTA = (w >> 8) & 0xFF;
    OSCR_NOP; OSCR_NOP;
    PORTH &= ~(1 << 5); PORTH &= ~(1 << 3);                             // /LWR e /CE0 baixos
    OSCR_NOP4; OSCR_NOP4; OSCR_NOP4;
    PORTH |= (1 << 3); PORTH |= (1 << 5);
    OSCR_NOP4; OSCR_NOP; OSCR_NOP;
    data_in();
  }
  void map_write(uint32_t a, uint16_t w) override {                     // writeSSF2Map do OSCR
    data_out();
    PORTJ |= (1 << 0);
    PORTL = (a >> 16) & 0xFF; PORTK = (a >> 8) & 0xFF; PORTF = a & 0xFF;
    PORTC = w & 0xFF; PORTA = (w >> 8) & 0xFF;
    OSCR_NOP; OSCR_NOP;
    PORTJ &= ~(1 << 0);                                                 // /TIME baixo
    PORTH &= ~(1 << 5);                                                 // /LWR baixo
    OSCR_NOP4; OSCR_NOP4; OSCR_NOP4;
    PORTH |= (1 << 5);
    PORTJ |= (1 << 0);
    data_in();
  }
};

struct AvrGbaBus : GbaBus {
  void begin() override {
    DDRH |= (1 << 0) | (1 << 3) | (1 << 5) | (1 << 6); PORTH |= (1 << 0) | (1 << 3) | (1 << 5) | (1 << 6);   // CS2, CS, WR, RD altos
    DDRF = 0xFF; DDRK = 0xFF; DDRC = 0xFF;
    delay(500);
  }
  void end() override { bus_release(); }
  uint16_t word(uint32_t byte_addr) override {
    DDRF = 0xFF; DDRK = 0xFF; DDRC = 0xFF;
    uint32_t a = byte_addr >> 1;
    PORTF = a & 0xFF; PORTK = (a >> 8) & 0xFF; PORTC = (a >> 16) & 0xFF;
    PORTH &= ~(1 << 3);                                                 // CS_ROM baixo: trava o endereço
    PORTF = 0; PORTK = 0; DDRF = 0; DDRK = 0;                           // barramento AD vira entrada
    PORTH &= ~(1 << 6);                                                 // RD baixo
    OSCR_NOP4; OSCR_NOP4;
    uint16_t w = (uint16_t(PINK) << 8) | PINF;
    PORTH |= (1 << 6); PORTH |= (1 << 3);
    return w;
  }
  uint8_t sram_read(uint16_t a) override {                              // readByte_GBA do OSCR
    DDRF = 0xFF; DDRK = 0xFF; DDRC = 0x00;
    PORTF = a & 0xFF; PORTK = a >> 8;
    PORTH &= ~(1 << 6); PORTH &= ~(1 << 0);                             // RD e CS2 baixos
    OSCR_NOP4; OSCR_NOP4;
    uint8_t v = PINC;
    PORTH |= (1 << 0); PORTH |= (1 << 6);
    return v;
  }
  void sram_write(uint16_t a, uint8_t v) override {                     // writeByte_GBA do OSCR
    DDRF = 0xFF; DDRK = 0xFF; DDRC = 0xFF;
    PORTF = a & 0xFF; PORTK = a >> 8; PORTC = v;
    OSCR_NOP4; OSCR_NOP4;
    PORTH &= ~(1 << 5); PORTH &= ~(1 << 0);                             // WR e CS2 baixos
    OSCR_NOP4; OSCR_NOP4; OSCR_NOP4; OSCR_NOP4;
    PORTH |= (1 << 5); PORTH |= (1 << 0);
    DDRC = 0x00;
  }
};

}  // namespace oscr
#endif  // ARDUINO && ATmega2560
