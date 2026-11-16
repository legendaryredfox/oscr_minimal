// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/SnesAcc.h: códigos dos acessórios do SNES (F-10, D178).
#include <stdio.h>
#include "../include/dumper/SnesAcc.h"

using namespace oscr::snesacc;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(isAcc(0x8001) && isAcc(0x8003) && isAcc(0xFFFF) && !isAcc(0) && !isAcc(4));          // o tipo de ROM forçado (0 a 4) nunca vira acessório
  CHECK(valid(kSufamiA) && valid(kSufamiB) && valid(kGpc) && !valid(0x8000) && !valid(0x8004) && !valid(0) && !valid(1));
  CHECK(isSufami(kSufamiA) && isSufami(kSufamiB) && !isSufami(kGpc) && sufamiSlotB(kSufamiB) && !sufamiSlotB(kSufamiA));
  CHECK(sufamiStartBank(false) == 32 && sufamiStartBank(true) == 64);
  CHECK(sufamiBytes(true) == 512UL * 1024 && sufamiBytes(false) == 1024UL * 1024 && kGpcBytes == 512UL * 1024);
  printf("test_snesacc: %d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
