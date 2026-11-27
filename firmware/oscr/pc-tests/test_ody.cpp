// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/OdyCore.h (Magnavox Odyssey 2, F-20, D226): tamanhos, mapper e classificação do slot.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/OdyCore.h"

using namespace oscr::ody;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(sizeIndex(2) == 0 && sizeIndex(4) == 1 && sizeIndex(8) == 2 && sizeIndex(12) == 3 && sizeIndex(16) == 4);
  CHECK(sizeIndex(0) == kBadIndex && sizeIndex(1) == kBadIndex && sizeIndex(6) == kBadIndex && sizeIndex(32) == kBadIndex && sizeIndex(2048) == kBadIndex);
  CHECK(mapperValid(0) && mapperValid(1) && !mapperValid(2) && !mapperValid(255));
  CHECK(argsValid(0, 2) && argsValid(0, 4) && argsValid(0, 8) && argsValid(0, 12) && argsValid(0, 16));
  CHECK(argsValid(1, 4) && !argsValid(1, 2) && !argsValid(1, 8) && !argsValid(1, 16));
  CHECK(!argsValid(2, 4) && !argsValid(0, 6));
  CHECK(fileBytes(0, 2) == 2048 && fileBytes(0, 12) == 12288 && fileBytes(0, 16) == 16384 && fileBytes(1, 4) == 4096);
  CHECK(fileBytes(1, 8) == 0 && fileBytes(3, 4) == 0 && fileBytes(0, 0) == 0);
  CHECK(kBase == 0x0400);

  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); b[7] = 0x12; CHECK(classify(b, 32) == kOk);
  memset(b, 0xFF, 32); b[31] = 0xFE; CHECK(classify(b, 32) == kOk);
  memset(b, 0x84, 32); CHECK(classify(b, 32) == kOk);
  CHECK(classify(b, 1) == kNoCart && classify(b, 0) == kNoCart);
  printf("%d verificacoes do Odyssey 2, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
