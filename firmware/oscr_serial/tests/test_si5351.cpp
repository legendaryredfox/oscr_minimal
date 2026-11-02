// SPDX-License-Identifier: GPL-3.0-or-later
#include <stdio.h>
#include <stdlib.h>
#include "../oscr_si5351.h"
using namespace oscr;
static int g_n = 0, g_fail = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

static void check_freq(uint64_t centihz, bool expect_int) {
  Si5351Synth s = si5351_synth(centihz);
  CHECK(s.ok);
  uint8_t r[8]; si5351_pack(s, s.r_div, r);
  uint64_t got = si5351_decode_centihz(r);
  double err = (double(got) - double(centihz)) / double(centihz);
  if (err < 0) err = -err;
  CHECK(err < 1e-6);                                                    // menos de 1 ppm
  if (expect_int) CHECK(s.b == 0);
  if (err >= 1e-6) printf("  %llu -> %llu\n", (unsigned long long)centihz, (unsigned long long)got);
}

int main() {
  // frequências que o OSCR usa no SNES (centésimos de Hz)
  check_freq(100000000ULL, true);        // 1 MHz  (CPU/CIC durante o desbloqueio)
  check_freq(400000000ULL, true);        // 4 MHz  (master durante o desbloqueio)
  check_freq(2147727200ULL, false);      // 21,477272 MHz
  check_freq(357954500ULL, false);       // 3,579545 MHz
  check_freq(307200000ULL, false);       // 3,072 MHz
  check_freq(3200000ULL, false);         // 32 kHz: precisa do divisor R
  // valores conhecidos: 900 MHz / 900 = 1 MHz => P1 = 128*900 - 512 = 114688, P2 = 0, P3 = 1
  Si5351Synth s = si5351_synth(100000000ULL);
  uint8_t r[8]; si5351_pack(s, s.r_div, r);
  CHECK(s.a == 900 && s.b == 0 && s.c == 1 && s.r_div == 0);
  CHECK(r[0] == 0 && r[1] == 1 && r[2] == 0x01 && r[3] == 0xC0 && r[4] == 0x00 && r[5] == 0 && r[6] == 0 && r[7] == 0);   // 114688 = 0x01C000
  // PLL: 25 MHz x 36 => a = 36: P1 = 128*36 - 512 = 4096 = 0x1000
  Si5351Synth pll = {SI5351_PLL_MULT, 0, 1, 0, true};
  si5351_pack(pll, 0, r);
  CHECK(r[1] == 1 && r[2] == 0 && r[3] == 0x10 && r[4] == 0x00);
  CHECK(!si5351_synth(0).ok);
  CHECK(!si5351_synth(100000000000ULL).ok);                             // 1 GHz: acima do possível
  printf("%d verificações do Si5351, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
