// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/TrsCore.h (TRS-80 Color Computer, F-20, D248): tabela de tamanhos, tamanho do arquivo, troca de banco e classificação do slot.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/TrsCore.h"

using namespace oscr::trs;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(sizeIndex(2) == 0 && sizeIndex(4) == 1 && sizeIndex(8) == 2 && sizeIndex(10) == 3);
  CHECK(sizeIndex(16) == 4 && sizeIndex(32) == 5 && sizeIndex(64) == 6 && sizeIndex(128) == 7);
  CHECK(sizeIndex(0) == kBadIndex && sizeIndex(1) == kBadIndex && sizeIndex(12) == kBadIndex && sizeIndex(256) == kBadIndex && sizeIndex(0xFFFF) == kBadIndex);
  for (uint8_t i = 0; i < kSizeCount; i++) CHECK(sizeIndex(sizeKb(i)) == i);
  CHECK(sizeKb(kSizeCount) == 0);
  CHECK(fileBytes(2) == 2048UL && fileBytes(10) == 10240UL && fileBytes(32) == 32768UL && fileBytes(128) == 131072UL);
  CHECK(fileBytes(0) == 0 && fileBytes(12) == 0);
  CHECK(!bankSwitched(16) && !bankSwitched(32) && bankSwitched(64) && bankSwitched(128) && !bankSwitched(0) && !bankSwitched(256));
  CHECK(kBase == 0xC000);

  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); b[7] = 0x12; CHECK(classify(b, 32) == kOk);
  memset(b, 0xFF, 32); b[31] = 0xFE; CHECK(classify(b, 32) == kOk);
  memset(b, 0x44, 32); CHECK(classify(b, 32) == kOk);
  CHECK(classify(b, 1) == kNoCart && classify(b, 0) == kNoCart);
  printf("%d verificacoes do TRS-80, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
