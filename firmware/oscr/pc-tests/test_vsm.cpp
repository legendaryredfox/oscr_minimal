// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/VsmCore.h (V.Smile, F-20, D228): tabela de tamanhos, tamanho do arquivo e classificação do slot.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/VsmCore.h"

using namespace oscr::vsm;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(sizeIndex(4096) == 0 && sizeIndex(6144) == 1 && sizeIndex(8192) == 2 && sizeIndex(16384) == 3);
  CHECK(sizeIndex(0) == kBadIndex && sizeIndex(4) == kBadIndex && sizeIndex(2048) == kBadIndex && sizeIndex(12288) == kBadIndex && sizeIndex(0xFFFF) == kBadIndex);
  for (uint8_t i = 0; i < kSizeCount; i++) CHECK(sizeIndex(sizeKb(i)) == i);
  CHECK(sizeKb(kSizeCount) == 0);
  CHECK(fileBytes(4096) == 0x400000UL && fileBytes(6144) == 0x600000UL && fileBytes(8192) == 0x800000UL && fileBytes(16384) == 0x1000000UL);
  CHECK(fileBytes(0) == 0 && fileBytes(1024) == 0);

  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); b[7] = 0x12; CHECK(classify(b, 32) == kOk);
  memset(b, 0xFF, 32); b[31] = 0xFE; CHECK(classify(b, 32) == kOk);
  memset(b, 0x5A, 32); CHECK(classify(b, 32) == kOk);
  CHECK(classify(b, 1) == kNoCart && classify(b, 0) == kNoCart);
  printf("%d verificacoes do V.Smile, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
