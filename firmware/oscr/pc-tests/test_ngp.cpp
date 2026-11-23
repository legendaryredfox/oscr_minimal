// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/NgpCore.h (Neo Geo Pocket, F-20, D202): classificação e tamanho.
#include <stdio.h>
#include "../include/dumper/NgpCore.h"

using namespace oscr::ngp;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(sizeKbValid(512) && sizeKbValid(1024) && sizeKbValid(2048) && sizeKbValid(4096));
  CHECK(!sizeKbValid(0) && !sizeKbValid(256) && !sizeKbValid(3072) && !sizeKbValid(8192));
  CHECK(classify(0xFFFF, false) == kNoCart && classify(0xFFFF, true) == kNoCart);
  CHECK(classify(0x982F, true) == kOk);        // Toshiba 16 Mbit com cabeçalho SNK
  CHECK(classify(0x982F, false) == kNoHeader);
  CHECK(classify(0x0000, false) == kNoHeader);
  CHECK(romBytes(2097152, 0) == 2097152);      // chip conhecido, PC não informou
  CHECK(romBytes(0, 0) == 0);                  // chip desconhecido: o PC precisa informar
  CHECK(romBytes(2097152, 4096) == 4194304);   // o PC vence
  CHECK(romBytes(0, 512) == 524288);
  printf("%d verificacoes do Neo Geo Pocket, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
