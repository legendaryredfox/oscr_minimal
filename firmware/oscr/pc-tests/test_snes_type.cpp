// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/SnesType.h (tipo de ROM do SNES forçado pelo PC, F-2). Os mesmos vetores estão em host/tests/test_snes_type.py e SnesTypeTest.kt.
#include <stdio.h>
#include "../include/dumper/SnesType.h"

using namespace OSCR::Dumper::SnesType;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(valid(0) && valid(1) && valid(4) && !valid(5) && !valid(256));
  CHECK(romType(kLoRom) == 0 && romType(kHiRom) == 1 && romType(kSa1) == 3 && romType(kExHiRom) == 4);
  CHECK(romType(kAuto) == 0xFF && romType(9) == 0xFF);
  // bancos: LoROM 32 KB, HiROM 64 KB por banco; SA-1 e ExHiROM 2 por Mbit (como o getCartInfo do OSCR)
  CHECK(numBanks(0, 8) == 32);          // 8 Mbit = 1 MB LoROM: 32 bancos de 32 KB
  CHECK(numBanks(0, 32) == 128);        // 4 MB LoROM
  CHECK(numBanks(1, 8) == 16);          // 1 MB HiROM: 16 bancos de 64 KB
  CHECK(numBanks(1, 32) == 64);
  CHECK(numBanks(4, 48) == 96);         // 6 MB ExHiROM
  CHECK(numBanks(3, 16) == 32);         // SA-1
  printf("%d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
