// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/MdExtra.h (RAM de backup do Sega CD, F-16). O tamanho vem do OSCR: byte baixo 4 = 2^4 * 8 KB = 128 KB; 6 = 512 KB.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/MdExtra.h"

using namespace OSCR::Dumper::MdExtra;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(bramSizeValid(0x20000UL) && bramSizeValid(0x80000UL));
  CHECK(!bramSizeValid(0) && !bramSizeValid(0x10000UL) && !bramSizeValid(0x40000UL));
  CHECK((1UL << 4) * 0x2000UL == 0x20000UL && (1UL << 6) * 0x2000UL == 0x80000UL);   // a conta do getCartInfo
  CHECK(kSaveBram == 5);
  CHECK(strlen(kBramName) < 32);                                                      // cabe no nome do DETECT
  printf("%d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
