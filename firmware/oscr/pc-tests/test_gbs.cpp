// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/GbSmartCore.h (GB Smart Card 32M, F-20, D249): índices aceitos, fim da lista e tamanho pelo código do cabeçalho.
#include <stdio.h>
#include "../include/dumper/GbSmartCore.h"

using namespace oscr::gbs;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(validIndex(0) && validIndex(1) && validIndex(126) && validIndex(kWhole));
  CHECK(!validIndex(127) && !validIndex(200) && !validIndex(0x100) && !validIndex(0xFFFF));
  CHECK(kWhole == 0xFF && kMaxGames < kWhole);
  CHECK(romBytes(0) == 32768UL && romBytes(1) == 65536UL && romBytes(5) == 1048576UL && romBytes(6) == 2097152UL && romBytes(8) == 8388608UL);
  CHECK(romBytes(9) == 0 && romBytes(0x52) == 0 && romBytes(0xFF) == 0);
  CHECK(!isEnd(0) && !isEnd(6) && !isEnd(8) && isEnd(9) && isEnd(0xFF));
  CHECK(kFlashBytes == 256UL * 16384UL);
  CHECK(kMaxPages * 6 >= kMaxGames);
  printf("%d verificacoes do GB Smart, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
