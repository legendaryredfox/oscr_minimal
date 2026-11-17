// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/MdBank.h: a conta do banco de 32 KiB (modelo do MAME) remonta a ROM inteira e as validações de tamanho.
#include <stdio.h>
#include <vector>
#include "../include/dumper/MdBank.h"

using namespace OSCR::Dumper::MdBank;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  CHECK(valid(1) && valid(2) && valid(3) && !valid(0) && !valid(4));
  CHECK(bankMask(kLionKing3) == 0xFF && bankMask(kPokemonStadium) == 0x7F);
  CHECK(sizeValid(kLionKing3, 2048) && sizeValid(kLionKing3, 4096) && sizeValid(kPokemonStadium, 4096) && sizeValid(kLionKing3, 128));
  CHECK(!sizeValid(kLionKing3, 64) && !sizeValid(kLionKing3, 3000) && !sizeValid(kLionKing3, 8192) && !sizeValid(0, 2048));
  CHECK(chunks(1, 2048) == 64 && chunks(2, 4096) == 128 && chunks(1, 128) == 4);
  // remonta a ROM: banco n e leitura de 0 a 0x7FFF devolvem os bytes n*0x8000 + a
  for (uint16_t m = 1; m <= 2; m++) {
    for (uint32_t kb = 128; kb <= 4096; kb *= 2) {
      bool ok = true;
      uint32_t bytes = kb * 1024UL;
      for (uint32_t n = 0; n < chunks(m, kb) && ok; n++)
        for (uint32_t a = 0; a < kChunkBytes; a += 0x1F3) if (romAddress(a, uint16_t(n), bytes) != n * kChunkBytes + a) { ok = false; break; }
      CHECK(ok);
    }
  }
  CHECK(kRegWordAddr * 2 == 0x700000UL);
  // Star Odyssey: base = n, pedaço de 256 KiB em $000000, tamanho em múltiplos de 256 KiB até 2 MiB
  CHECK(bankMask(kStarOdyssey) == 7 && chunkBytes(kStarOdyssey) == 0x40000UL && regWordAddr(kStarOdyssey) * 2 == 0xF00UL);
  CHECK(sizeValid(kStarOdyssey, 256) && sizeValid(kStarOdyssey, 1280) && sizeValid(kStarOdyssey, 2048));
  CHECK(!sizeValid(kStarOdyssey, 128) && !sizeValid(kStarOdyssey, 300) && !sizeValid(kStarOdyssey, 2304) && !sizeValid(kStarOdyssey, 4096));
  CHECK(chunks(kStarOdyssey, 1280) == 5 && chunks(kStarOdyssey, 2048) == 8);
  for (uint32_t kb = 256; kb <= 2048; kb += 256) {
    bool ok = true;
    for (uint32_t n = 0; n < chunks(kStarOdyssey, kb) && ok; n++) {
      uint16_t v = regValue(kStarOdyssey, n);
      if ((v & 0x8F) != 0) ok = false;                                  // só os bits 4 a 6: o bit 7 e os baixos ficam limpos
      for (uint32_t a = 0; a < kStarChunkBytes; a += 0x1F3) if (starAddress(a, v) != n * kStarChunkBytes + a) { ok = false; break; }
    }
    CHECK(ok);
  }
  printf("%d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
