// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/GbAcc.h (acessórios do Game Boy, F-17): faixa válida e tamanhos que as leituras do OSCR entregam.
#include <stdio.h>
#include "../include/dumper/GbAcc.h"

using namespace OSCR::Dumper::GbAcc;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(!valid(0) && valid(1) && valid(6) && !valid(7) && !valid(0x8001));
  CHECK(expectedBytes(kMegaMem) == 278528UL);
  CHECK(expectedBytes(kGameShark) == 131072UL);
  CHECK(expectedBytes(kGbMemory) == 1048576UL);
  CHECK(expectedBytes(kGbMemoryMap) == 128 && expectedBytes(kGbSmart) == 4UL * 1024 * 1024);
  CHECK(expectedBytes(kPelican) == 0 && expectedBytes(0) == 0);
  for (uint16_t a = 1; a <= kLast; a++) CHECK(valid(a));
  printf("%d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
