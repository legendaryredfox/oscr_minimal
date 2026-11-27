// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/MsxCore.h (MSX, F-20, D230): faixas dos mappers, índices de ROM e SRAM, tamanho do arquivo e classificação do slot.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/MsxCore.h"

using namespace oscr::msx;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  // sem mapper: 8, 16, 32 ou 64 KB
  CHECK(romIndex(0, 8) == 1 && romIndex(0, 16) == 2 && romIndex(0, 32) == 3 && romIndex(0, 64) == 4);
  CHECK(romIndex(0, 0) == kBadIndex && romIndex(0, 128) == kBadIndex && romIndex(0, 4) == kBadIndex);
  // ASCII8 64 a 512 KB, ASCII16 64 a 1024 KB, Konami com SCC 128 a 1024 KB, Koei 256 a 1024 KB
  CHECK(romIndex(1, 64) == 4 && romIndex(1, 512) == 7 && romIndex(1, 1024) == kBadIndex && romIndex(1, 32) == kBadIndex);
  CHECK(romIndex(2, 1024) == 8 && romIndex(9, 64) == kBadIndex && romIndex(9, 128) == 5);
  CHECK(romIndex(7, 128) == kBadIndex && romIndex(7, 256) == 6 && romIndex(7, 1024) == 8);
  // tamanhos fixos
  CHECK(romIndex(3, 64) == 4 && romIndex(4, 128) == 5 && romIndex(5, 1024) == 8 && romIndex(13, 128) == 5 && romIndex(10, 64) == 4);
  CHECK(romIndex(5, 512) == kBadIndex && romIndex(3, 32) == kBadIndex);
  // PAC: sem ROM (0 nunca vale); FM-PAC 64 KB
  CHECK(romIndex(11, 0) == kBadIndex && romIndex(11, 64) == 4 && romIndex(11, 32) == kBadIndex && romIndex(kPac, 8) == kBadIndex);
  // R-Type: 384 KB reais, índice 7 do núcleo
  CHECK(romIndex(kRType, 384) == 7 && romIndex(kRType, 512) == kBadIndex && romBytes(kRType, 384) == 384UL * 1024UL);
  // Bee Pack: 16 ou 32 KB
  CHECK(romIndex(14, 16) == 2 && romIndex(14, 32) == 3 && romIndex(14, 8) == kBadIndex);
  // mapper inexistente
  CHECK(romIndex(15, 64) == kBadIndex && romIndex(0x100, 64) == kBadIndex && romBytes(15, 64) == 0);
  CHECK(romBytes(0, 32) == 32768UL && romBytes(2, 1024) == 0x100000UL && romBytes(0, 128) == 0);

  // SRAM
  CHECK(hasSave(1) && hasSave(2) && hasSave(4) && hasSave(5) && hasSave(7) && hasSave(11));
  CHECK(!hasSave(0) && !hasSave(3) && !hasSave(6) && !hasSave(8) && !hasSave(9) && !hasSave(10) && !hasSave(12) && !hasSave(13) && !hasSave(14) && !hasSave(15));
  CHECK(ramIndex(1, 2) == 1 && ramIndex(1, 8) == 2 && ramIndex(1, 16) == kBadIndex && ramIndex(1, 0) == kBadIndex);
  CHECK(ramIndex(2, 2) == 1 && ramIndex(2, 8) == 2);
  CHECK(ramIndex(4, 8) == 2 && ramIndex(4, 2) == kBadIndex && ramIndex(5, 16) == 3 && ramIndex(5, 8) == kBadIndex);
  CHECK(ramIndex(kKoei, 8) == 2 && ramIndex(kKoei, 16) == kBadIndex && ramIndex(kKoei, 32) == 4);
  CHECK(ramIndex(11, 8) == 2 && ramIndex(0, 8) == kBadIndex && ramIndex(15, 8) == kBadIndex);
  CHECK(ramBytes(1, 2) == 2048UL && ramBytes(kKoei, 32) == 32768UL && ramBytes(5, 16) == 16384UL && ramBytes(3, 8) == 0);

  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); b[7] = 0x12; CHECK(classify(b, 32) == kOk);
  memset(b, 0x5A, 32); CHECK(classify(b, 32) == kOk);
  CHECK(classify(b, 1) == kNoCart && classify(b, 0) == kNoCart);
  b[0] = 0x41; b[1] = 0x42; CHECK(hasHeader(b, 32) && !hasHeader(b, 1));
  b[1] = 0x43; CHECK(!hasHeader(b, 32));
  printf("%d verificacoes do MSX, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
