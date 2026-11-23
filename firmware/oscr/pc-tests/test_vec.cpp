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

  // os trechos somam o tamanho do índice, e só os 64 KB usam o segundo banco
  for (uint8_t i = 0; i < kSizeCount; i++) {
    Seg s[8]; uint8_t n = segments(i, s); uint32_t total = 0; bool bank1 = false;
    for (uint8_t k = 0; k < n; k++) { total += uint32_t(s[k].end - s[k].start); if (s[k].bank) bank1 = true; }
    CHECK(total == uint32_t(sizeKb(i)) * 1024UL);
    CHECK(bank1 == (i == 5));
  }
  { Seg s[8]; CHECK(segments(0, s) == 1 && s[0].start == 0 && s[0].end == 0x1000); CHECK(segments(5, s) == 6 && s[5].bank == 1 && s[5].end == 0x8000); }

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
