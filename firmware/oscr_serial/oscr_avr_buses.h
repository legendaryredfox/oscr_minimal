// SPDX-License-Identifier: GPL-3.0-or-later
// HAL dos barramentos para o ATmega2560. As sequências de porta/bit vêm do OSCR
// (SNES.ino, NES.ino, MD.ino, GBA.ino, GPL v3) e os pinos conferem com docs/pinmap.md.
// NÃO VALIDADO EM HARDWARE: a lógica acima desta camada é testada no PC (tests/test_carts.cpp).
#pragma once
#if defined(ARDUINO) && defined(__AVR_ATmega2560__)
#include <Arduino.h>
#include <Wire.h>
#include <util/delay.h>

#include "oscr_bus.h"
#include "oscr_si5351.h"

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
  void cs(bool high) override { if (high) PORTH |= (1 << 3); else PORTH &= ~(1 << 3); }
  void wait_ms(uint16_t ms) override { delay(ms); }

  // ---- Si5351 (I²C 0x60, SDA D20 / SCL D21) e CIC (PG1 = reset do PIC). Sequências e frequências do OSCR (SNES.ino);
  // os registradores seguem o datasheet do Si5351 (AN619). NÃO VALIDADO EM HARDWARE.
  uint8_t clk_state_ = 0;                                              // 0 não testado, 1 presente, 2 ausente
  uint8_t clk_oe_ = 0xFF;                                              // registrador 3: bit = 1 desliga a saída
  bool clk_pll_ = false;
  bool i2c_write(uint8_t reg, const uint8_t* d, uint8_t n) {
    Wire.beginTransmission(0x60); Wire.write(reg);
    for (uint8_t i = 0; i < n; i++) Wire.write(d[i]);
    return Wire.endTransmission() == 0;
  }
  bool i2c_write1(uint8_t reg, uint8_t v) { return i2c_write(reg, &v, 1); }
  bool clocks_available() override {
    if (clk_state_ == 0) {
      Wire.begin();
#ifdef WIRE_HAS_TIMEOUT
      Wire.setWireTimeout(25000, true);                                // não trava se o barramento ficar preso
#endif
      Wire.beginTransmission(0x60);
      clk_state_ = (Wire.endTransmission() == 0) ? 1 : 2;
    }
    return clk_state_ == 1;
  }
  void si_set(uint8_t clk, uint64_t centihz) {                         // clk 0 a 2, PLLA fixo em 900 MHz
    if (!clk_pll_) {
      uint8_t p[8]; Si5351Synth pll = {SI5351_PLL_MULT, 0, 1, 0, true};
      si5351_pack(pll, 0, p);
      i2c_write1(183, 0xD2);                                           // carga do cristal: 10 pF
      i2c_write(26, p, 8);                                             // MSNA (PLLA)
      clk_pll_ = true;
    }
    Si5351Synth s = si5351_synth(centihz);
    if (!s.ok) return;
    uint8_t m[8]; si5351_pack(s, s.r_div, m);
    i2c_write(42 + 8 * clk, m, 8);                                     // MS0 = 42, MS1 = 50, MS2 = 58
    i2c_write1(16 + clk, s.b == 0 ? 0x4F : 0x0F);                      // ligado, modo inteiro se b = 0, fonte PLLA, saída do multisynth, 8 mA
    i2c_write1(177, 0xA0);                                             // reinicia o PLL
  }
  void si_oe(uint8_t mask_on, uint8_t mask_off) {
    clk_oe_ = (clk_oe_ & ~mask_on) | mask_off;
    i2c_write1(3, clk_oe_);
  }
  void clocks_boot() override {
    if (!clocks_available()) return;
    clk_oe_ = 0xFF; clk_pll_ = false;
    i2c_write1(3, 0xFF);                                               // todas as saídas desligadas
    for (uint8_t i = 0; i < 3; i++) i2c_write1(16 + i, 0x80);          // multisynths desligados
    si_set(1, 100000000ULL);                                           // CPU 1 MHz
    si_set(2, 100000000ULL);                                           // CIC 1 MHz
    si_set(0, 400000000ULL);                                           // master 4 MHz
    si_oe((1 << 2) | (1 << 0), 0);                                     // liga CIC e master; o clock do CPU fica desligado
    delay(500);
    DDRG |= (1 << 1); PORTG &= ~(1 << 1);                              // PG1 baixo: o PIC (CIC) começa a rodar
    delay(500);
  }
  void clocks_run() override {
    if (!clocks_available()) return;
    si_set(0, 2147727200ULL);                                          // master 21,477272 MHz
    si_set(1, 357954500ULL);                                           // CPU 3,579545 MHz
    si_set(2, 307200000ULL);                                           // CIC 3,072 MHz
  }
  void cpu_clock(bool on) override {
    if (!clocks_available()) return;
    if (on) si_oe(1 << 1, 0); else si_oe(0, 1 << 1);
  }
  void clocks_stop() override {
    DDRG |= (1 << 1); PORTG |= (1 << 1);                               // PG1 alto: CIC em reset
    if (clk_state_ == 1) { clk_oe_ = 0xFF; i2c_write1(3, 0xFF); }
  }
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
  uint8_t ram(uint16_t a) override {                                     // dumpMMC5RAM do OSCR: PHI2 baixo antes de cada leitura
    PORTF &= ~(1 << 0);
    return prg(a);
  }
  void ram_write(uint16_t a, uint8_t v) override {                       // write_wram_byte do OSCR
    PORTF &= ~(1 << 0);                                                 // PHI2 baixo
    PORTF |= (1 << 1);                                                  // ROMSEL alto
    set_address(a);
    PORTK = v;
    _delay_us(1);
    DDRK = 0xFF;                                                        // MODE_WRITE
    PORTF &= ~(1 << 7);                                                 // PRG_WRITE
    PORTF |= (1 << 0);                                                  // PHI2 alto
    _delay_us(1);
    PORTF &= ~(1 << 0);                                                 // PHI2 baixo
    PORTF |= (1 << 1);                                                  // ROMSEL alto
    PORTF |= (1 << 7);                                                  // PRG_READ
    PORTK = 0xFF; DDRK = 0;                                             // MODE_READ
    set_address(0);
    PORTF |= (1 << 0);                                                  // PHI2 alto
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
  // EEPROM serial do Mega Drive: EepromInit, writeWord_SDA, writeWord_SCL e writeWord_CM do OSCR. NÃO validado em hardware.
  static void eep_wait(bool slow) { if (slow) delayMicroseconds(100); else { OSCR_NOP4; OSCR_NOP4; OSCR_NOP4; } }
  static void eep_addr(uint32_t a) { PORTF = a & 0xFF; PORTK = (a >> 8) & 0xFF; PORTL = (a >> 16) & 0xFF; }
  void eep_enable(bool on) override {
    data_out();
    PORTF = 0x00; PORTK = 0x00; PORTL = 0x10; PORTA = 0x00;
    PORTH |= (1 << 0);                                                  // /RES alto
    PORTC = on ? 0 : 1;                                                 // 0 = liga a EEPROM, 1 = lê a ROM
    PORTH &= ~(1 << 3);                                                 // CE baixo
    PORTH &= ~(1 << 4) & ~(1 << 5);                                     // /UDSW e /LDSW baixos
    PORTH |= (1 << 6);                                                  // OE alto
    OSCR_NOP4; OSCR_NOP4; OSCR_NOP4;
    PORTH |= (1 << 4) | (1 << 5);
    OSCR_NOP4; OSCR_NOP4; OSCR_NOP4;
    data_in();
  }
  void eep_sda(uint32_t a, uint8_t d, bool slow) override {
    data_out(); eep_addr(a); PORTC = d;
    PORTH &= ~(1 << 3); PORTH &= ~(1 << 5); PORTH |= (1 << 4); PORTH |= (1 << 6);   // CE e /LDSW baixos
    eep_wait(slow);
    PORTH |= (1 << 5);
    eep_wait(slow);
    data_in();
  }
  void eep_scl(uint32_t a, uint8_t d, bool slow) override {
    data_out(); eep_addr(a); PORTC = d;
    PORTH &= ~(1 << 3); PORTH &= ~(1 << 4); PORTH |= (1 << 5); PORTH |= (1 << 6);   // CE e /UDSW baixos
    eep_wait(slow);
    PORTH |= (1 << 4);
    eep_wait(slow);
    data_in();
  }
  void wait_ms(uint16_t ms) override { delay(ms); }
  void eep_cm(uint32_t a, uint16_t w) override {
    data_out(); eep_addr(a); PORTC = w & 0xFF; PORTA = (w >> 8) & 0xFF;
    OSCR_NOP; OSCR_NOP;
    PORTH &= ~(1 << 4); PORTH &= ~(1 << 3);
    PORTH ^= (1 << 1);                                                  // pulso no clock
    OSCR_NOP4; OSCR_NOP4; OSCR_NOP4;
    PORTH ^= (1 << 1);
    PORTH |= (1 << 3); PORTH |= (1 << 4);
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
  // readBlock_EEP do OSCR para um bloco de 8 bytes. NÃO validado em hardware.
  void eeprom_send(uint16_t v, uint8_t nbits) {                         // send_GBA do OSCR
    for (uint8_t b = nbits; b > 0; b--) {
      if ((v >> (b - 1)) & 1) PORTF |= (1 << 0); else PORTF &= ~(1 << 0);
      PORTH &= ~(1 << 5); PORTH |= (1 << 5);                            // pulso em /WR
    }
  }
  void eeprom_block(uint16_t block, bool big, uint8_t out[8]) override {
    DDRH |= (1 << 3) | (1 << 5) | (1 << 6); DDRF |= (1 << 0); DDRC |= (1 << 7);
    PORTH |= (1 << 3) | (1 << 5) | (1 << 6); PORTF |= (1 << 0); PORTC |= (1 << 7);
    OSCR_NOP; OSCR_NOP;
    noInterrupts();
    PORTH &= ~(1 << 3);                                                 // CS_ROM baixo
    PORTF |= (1 << 0);                                                  // pedido de leitura "11"
    PORTH &= ~(1 << 5); PORTH |= (1 << 5);
    PORTH &= ~(1 << 5); PORTH |= (1 << 5);
    eeprom_send(block, big ? 14 : 6);
    PORTF &= ~(1 << 0);                                                 // bit de parada
    PORTH &= ~(1 << 5); PORTH |= (1 << 5);
    PORTH |= (1 << 3);
    OSCR_NOP4; OSCR_NOP4;
    DDRF &= ~(1 << 0);                                                  // A0 vira entrada
    PORTH &= ~(1 << 3);
    for (uint8_t i = 0; i < 4; i++) { PORTH &= ~(1 << 6); PORTH |= (1 << 6); }   // ignora 4 bits
    for (uint8_t j = 0; j < 8; j++) {
      uint8_t v = 0;
      for (uint8_t k = 0; k < 8; k++) { PORTH &= ~(1 << 6); PORTH |= (1 << 6); v = uint8_t((v << 1) | (PINF & 1)); }
      out[j] = v;
    }
    PORTH |= (1 << 3); PORTF |= (1 << 0); DDRF |= (1 << 0);
    interrupts();
    delayMicroseconds(200);
  }
  // writeBlock_EEP do OSCR para um bloco de 8 bytes. NÃO validado em hardware.
  bool eeprom_write_block(uint16_t block, bool big, const uint8_t in[8]) override {
    DDRH |= (1 << 3) | (1 << 5) | (1 << 6); DDRF |= (1 << 0); DDRC |= (1 << 7);
    PORTH |= (1 << 3) | (1 << 5) | (1 << 6); PORTF |= (1 << 0); PORTC |= (1 << 7);
    OSCR_NOP; OSCR_NOP;
    noInterrupts();
    PORTH &= ~(1 << 3);                                                 // CS_ROM baixo
    PORTF |= (1 << 0);                                                  // pedido de escrita "10"
    PORTH &= ~(1 << 5); PORTH |= (1 << 5);
    PORTF &= ~(1 << 0);
    PORTH &= ~(1 << 5); PORTH |= (1 << 5);
    eeprom_send(block, big ? 14 : 6);
    OSCR_NOP4; OSCR_NOP4;
    for (uint8_t j = 0; j < 8; j++) eeprom_send(in[j], 8);
    PORTF &= ~(1 << 0);                                                 // bit de parada
    PORTH &= ~(1 << 5); PORTH |= (1 << 5);
    PORTH |= (1 << 3);
    DDRF &= ~(1 << 0);                                                  // A0 vira entrada: pronto quando sobe
    bool ready = false;
    for (uint32_t n = 0; n < 100000UL && !ready; n++) {                 // o OSCR espera para sempre; aqui há limite
      PORTH &= ~((1 << 3) | (1 << 6));
      PORTH |= (1 << 3) | (1 << 6);
      ready = (PINF & 1) != 0;
    }
    DDRF |= (1 << 0);
    interrupts();
    delayMicroseconds(200);
    return ready;
  }
  void wait_ms(uint16_t ms) override { delay(ms); }
};

}  // namespace oscr
#endif  // ARDUINO && ATmega2560
