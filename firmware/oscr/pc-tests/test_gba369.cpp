// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/Gba369.h: leitura do 369-in-1 (F-18, D174).
#include <stdio.h>
#include "../include/dumper/Gba369.h"

using namespace oscr::gba369;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(code(0) == 0x8000 && code(63) == 0xBF00);
  CHECK(isRead(code(5)) && !isRead(1) && !isRead(6));          // mapper comum de GBA (tipo de save) nunca vira leitura 369
  CHECK(block(code(37)) == 37);

  CHECK(valid(code(0), 0) && bytes(0) == 256UL << 20);        // Read 256MB
  CHECK(!valid(code(1), 0));                                  // tamanho 0 só no bloco 0
  CHECK(valid(code(0), 32) && bytes(32) == 32UL << 20);
  CHECK(valid(code(8), 32));                                  // bloco 8 = início do 2º banco de 32 MB
  CHECK(!valid(code(1), 32));                                 // passaria do fim do banco
  CHECK(valid(code(7), 4));                                   // último bloco de 4 MB do 1º banco
  CHECK(!valid(code(7), 8));
  CHECK(valid(code(63), 4) && !valid(code(63), 8));
  CHECK(valid(code(2), 1) && valid(code(2), 3));              // menos de 4 MB: um bloco só
  CHECK(!valid(code(2), 6) && !valid(code(2), 5));            // 4 MB ou mais: múltiplo de 4
  CHECK(!valid(code(0), 33));
  CHECK(!valid(0x8001, 4) && !valid(0xC000, 4));              // bits de fora
  CHECK(!valid(0x0000, 4));                                   // sem o flag
  printf("%d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
