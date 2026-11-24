// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/ArcCore.h (Emerson Arcadia 2001, F-20, D215): tabela de tamanhos, trechos de leitura e classificação.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/ArcCore.h"

using namespace oscr::arc;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(sizeKb(0) == 2 && sizeKb(1) == 4 && sizeKb(2) == 6 && sizeKb(3) == 8 && sizeKb(4) == 0 && sizeKb(255) == 0);
  for (uint8_t i = 0; i < kSizeCount; i++) CHECK(sizeIndex(sizeKb(i)) == i);
  CHECK(sizeIndex(0) == kBadIndex && sizeIndex(1) == kBadIndex && sizeIndex(3) == kBadIndex && sizeIndex(16) == kBadIndex);

  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); b[7] = 0x12; CHECK(classify(b, 32) == kOk);
  memset(b, 0xFF, 32); b[31] = 0xFE; CHECK(classify(b, 32) == kOk);
  memset(b, 0x55, 32); CHECK(classify(b, 32) == kOk);            // valor único que não é $00 nem $FF não conta como vazio
  CHECK(classify(b, 1) == kNoCart && classify(b, 0) == kNoCart);
  printf("%d verificacoes do Arcadia 2001, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
