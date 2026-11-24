// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/VecCore.h (Vectrex, F-20, D205): tabela de tamanhos, trechos de leitura e classificação.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/VecCore.h"

using namespace oscr::vec;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(sizeKb(0) == 4 && sizeKb(1) == 8 && sizeKb(2) == 12 && sizeKb(3) == 16 && sizeKb(4) == 32 && sizeKb(5) == 64 && sizeKb(6) == 0);
  for (uint8_t i = 0; i < kSizeCount; i++) CHECK(sizeIndex(sizeKb(i)) == i);
  CHECK(sizeIndex(0) == kBadIndex && sizeIndex(2) == kBadIndex && sizeIndex(20) == kBadIndex && sizeIndex(128) == kBadIndex);

  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x11, 32); b[0] = 0x67; CHECK(classify(b, 32) == kOk);
  b[0] = 0x00; b[1] = 0x01; CHECK(classify(b, 32) == kNoHeader);
  memset(b, 0x67, 32); CHECK(classify(b, 32) == kOk);
  CHECK(classify(b, 1) == kNoCart);
  printf("%d verificacoes do Vectrex, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
