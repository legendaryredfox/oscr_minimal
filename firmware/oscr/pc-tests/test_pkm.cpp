// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/PkmCore.h (Pokémon Mini, F-20, D227): tamanho fixo, prg_kb aceito e classificação do slot.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/PkmCore.h"

using namespace oscr::pkm;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(kRomBytes == 524288UL);
  CHECK(kBase == 0x2100UL && kBase < kRomBytes);
  CHECK(sizeValid(0) && sizeValid(512));
  CHECK(!sizeValid(1) && !sizeValid(256) && !sizeValid(1024) && !sizeValid(0xFFFF));

  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); b[5] = 0x4D; CHECK(classify(b, 32) == kOk);
  memset(b, 0xFF, 32); b[31] = 0x00; CHECK(classify(b, 32) == kOk);
  memset(b, 0x4E, 32); CHECK(classify(b, 32) == kOk);
  CHECK(classify(b, 1) == kNoCart && classify(b, 0) == kNoCart);
  printf("%d verificacoes do Pokemon Mini, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
