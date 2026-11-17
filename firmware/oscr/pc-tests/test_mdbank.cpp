// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/MdBank.h: a conta do banco de 32 KiB (modelo do MAME) remonta a ROM inteira e as validações de tamanho.
#include <stdio.h>
#include <vector>
#include "../include/dumper/MdBank.h"

using namespace OSCR::Dumper::MdBank;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(valid(1) && valid(2) && !valid(0) && !valid(3));
  CHECK(bankMask(kLionKing3) == 0xFF && bankMask(kPokemonStadium) == 0x7F);
  CHECK(sizeValid(kLionKing3, 2048) && sizeValid(kLionKing3, 4096) && sizeValid(kPokemonStadium, 4096) && sizeValid(kLionKing3, 128));
  CHECK(!sizeValid(kLionKing3, 64) && !sizeValid(kLionKing3, 3000) && !sizeValid(kLionKing3, 8192) && !sizeValid(0, 2048));
  CHECK(chunks(2048) == 64 && chunks(4096) == 128 && chunks(128) == 4);
  // remonta a ROM: banco n e leitura de 0 a 0x7FFF devolvem os bytes n*0x8000 + a
  for (uint16_t m = 1; m <= 2; m++) {
    for (uint32_t kb = 128; kb <= 4096; kb *= 2) {
      bool ok = true;
      uint32_t bytes = kb * 1024UL;
      for (uint32_t n = 0; n < chunks(kb) && ok; n++)
        for (uint32_t a = 0; a < kChunkBytes; a += 0x1F3) if (romAddress(a, uint16_t(n), bytes) != n * kChunkBytes + a) { ok = false; break; }
      CHECK(ok);
    }
  }
  CHECK(kRegWordAddr * 2 == 0x700000UL);
  printf("%d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
