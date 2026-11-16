// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/NesCore.h: cartucho ausente (F-15, D173).
#include <stdio.h>
#include <string.h>
#include "../include/dumper/NesCore.h"

using namespace oscr::nes;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  uint8_t a[64], b[16], c[64], d[16];
  auto fill = [&](uint8_t v) { memset(a, v, 64); memset(b, v, 16); memset(c, v, 64); memset(d, v, 16); };
  auto absent = [&]() { return cartAbsent(a, 64, b, 16, c, 64, d, 16); };

  fill(0xFF); CHECK(absent());
  fill(0x00); CHECK(absent());
  fill(0x55); CHECK(!absent());                        // valor único que não é $00 nem $FF
  fill(0xFF); a[10] = 0x4E; CHECK(!absent());          // dado em $8000
  fill(0xFF); c[63] = 0x01; CHECK(!absent());          // dado em $C000
  fill(0xFF); b[0] = 0x00; CHECK(!absent());           // janela nova $A000 com outro valor
  fill(0xFF); d[12] = 0x80; d[13] = 0xC0; CHECK(!absent());   // $8000 e $C000 em branco, mas o vetor RESET está gravado: há cartucho
  fill(0x00); d[0] = 0xFF; CHECK(!absent());           // janelas com valores diferentes entre si
  printf("%d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
