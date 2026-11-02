// SPDX-License-Identifier: GPL-3.0-or-later
// Cálculo dos registradores do Si5351 (módulo breakout com cristal de 25 MHz). Parte portátil do driver:
// o I²C fica em oscr_avr_buses.h. Layout dos registradores conforme o datasheet Si5351A/B/C e a nota AN619.
// NÃO VALIDADO EM HARDWARE; só o cálculo é testado no PC (tests/test_si5351.cpp).
#pragma once
#include <stdint.h>

namespace oscr {

const uint32_t SI5351_XTAL_HZ = 25000000UL;     // cristal dos módulos Adafruit e similares
const uint8_t SI5351_PLL_MULT = 36;             // PLLA = 25 MHz x 36 = 900 MHz (dentro de 600 a 900 MHz)
const uint32_t SI5351_PLL_HZ = SI5351_XTAL_HZ * SI5351_PLL_MULT;

// Parâmetros de um multisynth: saída = PLL / (a + b/c) / 2^r_div.
struct Si5351Synth {
  uint32_t a, b, c;
  uint8_t r_div;          // 0 a 7 (divide por 1, 2, 4 ... 128)
  bool ok;
};

// freq_centihz = frequência em centésimos de Hz (a unidade que o OSCR usa: 100000000 = 1 MHz).
static inline Si5351Synth si5351_synth(uint64_t freq_centihz) {
  Si5351Synth s = {0, 0, 1, 0, false};
  if (freq_centihz == 0) return s;
  uint64_t f = freq_centihz;                                            // sobe a frequência com o divisor R até o multisynth aceitar (a <= 1800)
  const uint64_t pll = uint64_t(SI5351_PLL_HZ) * 100ULL;
  while (s.r_div < 7 && pll / f > 1800ULL) { f <<= 1; s.r_div++; }
  if (pll / f < 6ULL || pll / f > 1800ULL) return s;                    // fora de 6 a 1800
  s.c = 1048575UL;                                                      // máximo de 20 bits
  s.a = uint32_t(pll / f);
  uint64_t rem = pll - uint64_t(s.a) * f;                               // resto: b/c = rem / f
  s.b = uint32_t((rem * s.c + f / 2) / f);
  if (s.b >= s.c) { s.a++; s.b = 0; }
  if (s.b == 0) s.c = 1;
  s.ok = s.a >= 6 && s.a <= 1800;
  return s;
}

// Os 8 bytes de um multisynth (MSx) ou do PLL (MSNx), a partir de P1, P2, P3.
static inline void si5351_pack(const Si5351Synth& s, uint8_t r_div, uint8_t out[8]) {
  uint32_t p3 = s.c;
  uint32_t t = uint32_t((uint64_t(128) * s.b) / s.c);
  uint32_t p1 = 128UL * s.a + t - 512UL;
  uint32_t p2 = 128UL * s.b - s.c * t;
  out[0] = uint8_t(p3 >> 8);
  out[1] = uint8_t(p3);
  out[2] = uint8_t(((r_div & 7) << 4) | ((p1 >> 16) & 3));             // R_DIV em 6:4, MSx_DIVBY4 em 3:2 (0), P1 em 1:0
  out[3] = uint8_t(p1 >> 8);
  out[4] = uint8_t(p1);
  out[5] = uint8_t(((p3 >> 16) & 0x0F) << 4 | ((p2 >> 16) & 0x0F));
  out[6] = uint8_t(p2 >> 8);
  out[7] = uint8_t(p2);
}

// Inverso, só para o teste: frequência (em centésimos de Hz) que os 8 bytes geram.
static inline uint64_t si5351_decode_centihz(const uint8_t r[8]) {
  uint32_t p3 = (uint32_t(r[5] & 0xF0) << 12) | (uint32_t(r[0]) << 8) | r[1];
  uint32_t p1 = (uint32_t(r[2] & 3) << 16) | (uint32_t(r[3]) << 8) | r[4];
  uint32_t p2 = (uint32_t(r[5] & 0x0F) << 16) | (uint32_t(r[6]) << 8) | r[7];
  uint8_t rd = (r[2] >> 4) & 7;
  // a + b/c = (p1 + 512 + p2/p3) / 128
  double mult = (double(p1) + 512.0 + double(p2) / double(p3)) / 128.0;
  return uint64_t(double(SI5351_PLL_HZ) * 100.0 / mult / double(1u << rd) + 0.5);
}

}  // namespace oscr
