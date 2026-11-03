// SPDX-License-Identifier: GPL-3.0-or-later
// Roda o HAL do AVR (oscr_avr_buses.h) no PC com registradores simulados e confere as sequências de porta contra o que o OSCR faz
// e contra docs/pinmap.md. Não valida tempos nem níveis elétricos (isso só com hardware).
#include <stdio.h>
#include <string>
#include "avr_mock/Arduino.h"
#include "avr_mock/Wire.h"
#define ARDUINO 1
#define __AVR_ATmega2560__ 1
#include "../oscr_avr_buses.h"

using namespace oscr;
static int g_n = 0, g_fail = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

typedef std::vector<std::pair<const char*, uint8_t> > Trace;
static void reset_regs() {
  HalReg* all[] = {&PORTA, &DDRA, &PINA, &PORTC, &DDRC, &PINC, &PORTD, &DDRD, &PIND, &PORTE, &DDRE, &PINE, &PORTF, &DDRF, &PINF,
                   &PORTG, &DDRG, &PING, &PORTH, &DDRH, &PINH, &PORTJ, &DDRJ, &PINJ, &PORTK, &DDRK, &PINK, &PORTL, &DDRL, &PINL};
  for (HalReg* r : all) r->v = 0;
  hal_trace().clear();
}
// há, no trace, um valor de `reg` com o bit em `level` seguido (depois) de outro com o bit no nível oposto?
static bool pulse(const char* reg, uint8_t bit, bool first_level) {
  const Trace& t = hal_trace(); int state = 0;
  for (size_t i = 0; i < t.size(); i++) {
    if (std::string(t[i].first) != reg) continue;
    bool lv = (t[i].second >> bit) & 1;
    if (state == 0 && lv == first_level) state = 1;
    else if (state == 1 && lv != first_level) return true;
  }
  return false;
}
static bool bit(const HalReg& r, uint8_t b) { return (r.v >> b) & 1; }
static bool seq(const char* reg, uint8_t a, uint8_t b) {                      // duas atribuições seguidas ao mesmo registrador: a e depois b
  const Trace& t = hal_trace(); int last = -1; uint8_t prev = 0;
  for (size_t i = 0; i < t.size(); i++) {
    if (std::string(t[i].first) != reg) continue;
    if (last >= 0 && prev == a && t[i].second == b) return true;
    last = int(i); prev = t[i].second;
  }
  return false;
}

static void test_snes() {
  reset_regs(); AvrSnesBus s; s.begin();
  CHECK(DDRF.v == 0xFF && DDRK.v == 0xFF && DDRL.v == 0xFF && DDRA.v == 0xFF && DDRC.v == 0);   // A0-A15, BA0-BA7, PA0-PA7 saída; dados entrada
  CHECK(bit(PORTH, 0) && bit(PORTH, 5) && !bit(PORTH, 3) && !bit(PORTH, 6));                   // RST e WR altos; CS e RD baixos
  CHECK(!bit(PORTE, 5));                                                                       // REFRESH baixo (SA-1)
  PINC.v = 0xA5;
  CHECK(s.read(0x12, 0x3456) == 0xA5 && PORTL.v == 0x12 && PORTF.v == 0x56 && PORTK.v == 0x34); // endereço: banco em PL, A0-A7 em PF, A8-A15 em PK
  hal_trace().clear();
  s.write(0xC0, 0x1234, 0x77);
  CHECK(pulse("PORTH", 5, false));                                                             // WR baixo e depois alto
  CHECK(PORTC.v == 0x77 && PORTL.v == 0xC0 && DDRC.v == 0 && bit(PORTH, 5) && !bit(PORTH, 6));  // dado no PC; volta a leitura (RD baixo)
  s.cs(true); CHECK(bit(PORTH, 3)); s.cs(false); CHECK(!bit(PORTH, 3));
  s.end(); CHECK(DDRF.v == 0 && DDRK.v == 0 && DDRL.v == 0);                                    // solta o barramento
}

static void test_nes() {
  reset_regs(); AvrNesBus n; n.begin();
  CHECK(DDRL.v == 0xFF && DDRA.v == 0xFF && DDRK.v == 0 && DDRF.v == 0b10110111);
  PINK.v = 0x5A;
  CHECK(n.prg(0x8123) == 0x5A && PORTL.v == 0x23 && PORTA.v == 0x81);                           // A0-A7 em PL, A8-A15 em PA
  CHECK(bit(PORTF, 0) && !bit(PORTF, 1));                                                       // PHI2 alto; /ROMSEL baixo (>= $8000)
  n.prg(0x6123); CHECK(bit(PORTF, 0) && bit(PORTF, 1));                                         // abaixo de $8000: /ROMSEL alto
  n.prg(0x2000); CHECK(!bit(PORTF, 4));                                                         // A13 alto = /A13 do CHR baixo
  n.prg(0x1000); CHECK(bit(PORTF, 4));
  hal_trace().clear();
  n.prg_write(0x8000, 0x33);
  CHECK(pulse("PORTF", 7, false));                                                              // R/W baixo durante a escrita e volta a alto
  CHECK(pulse("PORTF", 0, true));                                                               // PHI2 sobe e desce
  CHECK(PORTF.v & (1 << 7) && DDRK.v == 0);                                                     // de volta à leitura
  hal_trace().clear();
  n.reg_write_safe(0xE000, 0x01);
  CHECK(seq("PORTF", 0b01111101, 0b01111110));                                                  // /ROMSEL baixo + M2 alto, depois /ROMSEL alto + M2 baixo, seguidos (write_reg_byte)
  CHECK(PORTK.v == 0xFF && DDRK.v == 0 && bit(PORTF, 0));
  hal_trace().clear();
  n.ram_write(0x6000, 0x44);                                                                    // write_wram_byte: ROMSEL sempre alto, M2 sobe uma vez
  CHECK(pulse("PORTF", 0, true) && bit(PORTF, 1) && bit(PORTF, 7));
  hal_trace().clear();
  PINK.v = 0x99; CHECK(n.chr(0x1234) == 0x99 && PORTL.v == 0x34 && PORTA.v == 0x12);
  CHECK(pulse("PORTF", 5, false));                                                              // /RD do CHR pulsa
}

static void test_gb() {
  reset_regs(); AvrGbBus g; g.begin();
  CHECK(DDRF.v == 0xFF && DDRK.v == 0xFF && DDRC.v == 0);
  CHECK(bit(PORTH, 0) && !bit(PORTH, 1) && bit(PORTH, 3) && bit(PORTH, 5) && bit(PORTH, 6));    // RST alto no fim; CLK baixo; CS, WR, RD altos
  CHECK(pulse("PORTH", 0, false) && hal_delay_ms() >= 400);                                     // RST baixo, 400 ms, alto
  PINC.v = 0x3C;
  hal_trace().clear();
  CHECK(g.read(0x0147) == 0x3C && PORTF.v == 0x47 && PORTK.v == 0x01);
  CHECK(pulse("PORTH", 6, false) && bit(PORTH, 6));                                             // RD baixo e depois alto
  hal_trace().clear();
  g.write(0x2100, 0x05);
  CHECK(pulse("PORTH", 5, false) && bit(PORTH, 5) && PORTC.v == 0xFF && DDRC.v == 0);           // WR baixo e depois alto; dados soltos
  hal_trace().clear();
  g.sram_read(0xA000, false); CHECK(bit(PORTH, 3) && bit(PORTH, 1) && pulse("PORTH", 3, false)); // CS e CLK baixos durante, altos no fim
  g.sram_read(0xA000, true);  CHECK(bit(PORTH, 3) && !bit(PORTH, 1));                           // GB Camera: só o CS sobe de novo; CLK fica baixo
  hal_trace().clear();
  g.sram_write(0xA001, 0x12, true);                                                             // câmera: CS baixo, CLK alto, WR baixo...
  CHECK(pulse("PORTH", 1, true) && bit(PORTH, 3) && bit(PORTH, 5) && !bit(PORTH, 1));           // ... e no fim CS e WR altos, CLK baixo
  g.sram_write(0xA001, 0x12, false); CHECK(bit(PORTH, 3) && bit(PORTH, 5) && bit(PORTH, 1));
}

static void test_clocks() {
  reset_regs(); Wire.tx.clear(); Wire.ack = true;
  AvrSnesBus s;
  CHECK(s.clocks_available() && Wire.begins == 1);
  CHECK(!bit(PORTD, 0) && !bit(PORTD, 1));                                                      // sem pull-up interno no SDA/SCL (5 V)
  Wire.tx.clear(); s.clocks_boot();
  bool oe_off = false, load = false, reset = false;
  for (auto& f : Wire.tx) {
    if (f.size() == 2 && f[0] == 3 && f[1] == 0xFF) oe_off = true;
    if (f.size() == 2 && f[0] == 183 && f[1] == 0xD2) load = true;
    if (f.size() == 2 && f[0] == 177 && f[1] == 0xA0) reset = true;
  }
  CHECK(oe_off && load && reset);
  CHECK(!bit(PORTG, 1) && bit(DDRG, 1));                                                        // PG1 baixo: o PIC (CIC) roda
  // saídas: depois do boot só CLK0 (bit 0) e CLK2 (bit 2) ligadas; CLK1 (CPU) desligada
  uint8_t last_oe = 0xFF; for (auto& f : Wire.tx) if (f.size() == 2 && f[0] == 3) last_oe = f[1];
  CHECK(last_oe == uint8_t(~((1 << 0) | (1 << 2))));
  Wire.tx.clear(); s.cpu_clock(true);
  CHECK(!Wire.tx.empty() && Wire.tx.back()[0] == 3 && !(Wire.tx.back()[1] & (1 << 1)));         // CLK1 ligada
  s.clocks_stop(); CHECK(bit(PORTG, 1));                                                        // CIC em reset
  { AvrSnesBus s2; Wire.ack = false; CHECK(!s2.clocks_available()); }                           // módulo ausente
}

int main() {
  test_snes(); test_nes(); test_gb(); test_clocks();
  printf("%d verificações do HAL do AVR, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
