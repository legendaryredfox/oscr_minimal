// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/RcaCore.h (RCA Studio II, F-20, D216): tamanho oferecido e classificação do slot.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/RcaCore.h"

using namespace oscr::rca;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(sizeIndex(1) == 1);
  CHECK(sizeIndex(0) == kBadIndex && sizeIndex(2) == kBadIndex && sizeIndex(4) == kBadIndex && sizeIndex(512) == kBadIndex);
  CHECK(kBase == 0x0400);

  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); b[7] = 0x12; CHECK(classify(b, 32) == kOk);
  memset(b, 0xFF, 32); b[31] = 0xFE; CHECK(classify(b, 32) == kOk);
  memset(b, 0x55, 32); CHECK(classify(b, 32) == kOk);
  CHECK(classify(b, 1) == kNoCart && classify(b, 0) == kNoCart);
  printf("%d verificacoes do RCA Studio II, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
