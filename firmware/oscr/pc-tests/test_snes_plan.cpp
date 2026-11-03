// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/SnesPlan.h (plano de gravação do flash CFI do SNES). Os mesmos vetores estão em host/tests/test_rom_write.py
// (snes_plan do romimage.py) e em RomWriteTest.kt: se a regra mudar, os três falham juntos.
#include <stdio.h>
#include "../include/dumper/SnesPlan.h"

using namespace OSCR::Dumper::SnesFlash;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

static bool seg(Seg const & s, uint8_t chip, uint32_t addr, uint32_t len) { return s.chip == chip && s.addr == addr && s.len == len; }

int main() {
  Seg s[4];
  const uint32_t M = kMB;

  // 1 chip
  CHECK(plan(kLayout1x, 1 * M, 2 * M, s) == 1 && seg(s[0], 1, 0, 1 * M));
  CHECK(plan(kLayout1x, 3 * M, 4 * M, s) == 1 && seg(s[0], 1, 0, 3 * M));
  CHECK(plan(kLayout1x, 3 * M, 2 * M, s) == 0);                 // não cabe
  CHECK(plan(kLayout1x, 1 * M, 3 * M, s) == 0);                 // capacidade que não existe
  CHECK(plan(kLayout1x, 1000, 2 * M, s) == 0);                  // não é múltiplo de 512

  // 2x 2MB
  CHECK(plan(kLayout2x2, 1 * M, 0, s) == 2 && seg(s[0], 1, 0, 1 * M) && seg(s[1], 2, 0, 0));
  CHECK(plan(kLayout2x2, 3 * M, 0, s) == 2 && seg(s[0], 1, 0, 2 * M) && seg(s[1], 2, 0, 1 * M));
  CHECK(plan(kLayout2x2, 4 * M, 0, s) == 2 && seg(s[0], 1, 0, 2 * M) && seg(s[1], 2, 0, 2 * M));
  CHECK(plan(kLayout2x2, 5 * M, 0, s) == 0);

  // 2x 4MB (invertido, 6 a 8 MB)
  CHECK(plan(kLayout2x4, 8 * M, 0, s) == 2 && seg(s[0], 1, 0, 4 * M) && seg(s[1], 2, 0, 4 * M));
  CHECK(plan(kLayout2x4, 6 * M, 0, s) == 2 && seg(s[0], 1, 0, 2 * M) && seg(s[1], 2, 0, 4 * M));
  CHECK(plan(kLayout2x4, 4 * M, 0, s) == 0);

  // 4x 2MB
  CHECK(plan(kLayout4x2, 8 * M, 0, s) == 4 && seg(s[0], 1, 0, 2 * M) && seg(s[1], 2, 0, 2 * M) && seg(s[2], 3, 0, 2 * M) && seg(s[3], 4, 0, 2 * M));
  CHECK(plan(kLayout4x2, 6 * M, 0, s) == 4 && seg(s[0], 1, 0, 2 * M) && seg(s[1], 2, 0, 0) && seg(s[2], 3, 0, 2 * M) && seg(s[3], 4, 0, 2 * M));
  CHECK(plan(kLayout4x2, 2 * M, 0, s) == 0);

  // 1x 8MB (metades trocadas)
  CHECK(plan(kLayout1x8, 8 * M, 0, s) == 2 && seg(s[0], 1, 0, 4 * M) && seg(s[1], 1, 4 * M, 4 * M));
  CHECK(plan(kLayout1x8, 6 * M, 0, s) == 2 && seg(s[0], 1, 0, 2 * M) && seg(s[1], 1, 4 * M, 4 * M));
  CHECK(plan(kLayout1x8, 7 * M, 0, s) == 0);

  CHECK(plan(kGeneric, 1 * M, 0, s) == 0 && plan(9, 1 * M, 0, s) == 0);
  CHECK(chipCount(kLayout1x) == 1 && chipCount(kLayout2x2) == 2 && chipCount(kLayout2x4) == 2 && chipCount(kLayout4x2) == 4 && chipCount(kLayout1x8) == 1);
  CHECK(chipBytes(kLayout2x2, 0) == 2 * M && chipBytes(kLayout1x8, 0) == 8 * M && chipBytes(kLayout1x, 4 * M) == 4 * M && chipBytes(kLayout1x, 1 * M) == 0);

  printf("%d verificações do plano do SNES, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
