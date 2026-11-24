// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/AtariCore.h (Atari 2600, F-20, D206): ids de mapper, tamanhos e classificação.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/AtariCore.h"

using namespace oscr::a26;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  uint8_t n; Map const * t = table(n);
  CHECK(n == 23);
  for (uint8_t i = 0; i < n; i++) for (uint8_t k = i + 1; k < n; k++) CHECK(t[i].id != t[k].id);   // nenhum id repetido
  CHECK(mapperKb(0x40) == 4 && mapperKb(0xF8) == 8 && mapperKb(0x08) == 8 && mapperKb(0xF6) == 16 && mapperKb(0xF4) == 32 && mapperKb(0xF0) == 64);
  CHECK(mapperKb(0x20) == 2 && mapperKb(0xC0) == 2 && mapperKb(0x3F) == 8 && mapperKb(0x3E) == 32 && mapperKb(0xD0) == 10 && mapperKb(0xFA) == 12);
  CHECK(mapperKb(0xDF) == 128 && mapperKb(0xBA) == 128 && mapperKb(0xBB) == 256 && mapperKb(0x07) == 64);
  CHECK(mapperKb(0xE7) == kVariable && mapperValid(0xE7));
  CHECK(mapperKb(0x00) == kUnknown && mapperKb(0x41) == kUnknown && mapperKb(0x1234) == kUnknown && !mapperValid(0xFF));
  uint8_t b[32];
  memset(b, 0xFF, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0x00, 32); CHECK(classify(b, 32) == kNoCart);
  memset(b, 0xA5, 32); CHECK(classify(b, 32) == kOk);      // valor único que não é $00 nem $FF
  memset(b, 0xFF, 32); b[31] = 0x00; CHECK(classify(b, 32) == kOk);
  CHECK(classify(b, 1) == kNoCart);
  // Atari 5200 e 7800 (D209)
  using namespace oscr::atari;
  CHECK(a52Kb(0, 4) == 4 && a52Kb(0, 8) == 8 && a52Kb(0, 16) == 16 && a52Kb(0, 32) == 32 && a52Kb(0, 12) == 0 && a52Kb(0, 0) == 0);
  CHECK(a52Kb(1, 0) == 16 && a52Kb(1, 99) == 16 && a52Kb(2, 0) == 40 && a52Kb(3, 16) == 0);
  CHECK(a78Kb(0, 16) == 16 && a78Kb(0, 32) == 32 && a78Kb(0, 48) == 48 && a78Kb(0, 64) == 0 && a78Kb(0, 8) == 0);
  CHECK(a78Kb(1, 0) == 128 && a78Kb(2, 0) == 144 && a78Kb(3, 0) == 64 && a78Kb(4, 0) == 128 && a78Kb(5, 0) == 64 && a78Kb(6, 0) == 64 && a78Kb(8, 0) == 144 && a78Kb(9, 16) == 0);
  CHECK(a78Kb(7, 32) == 64 && a78Kb(7, 48) == 96 && a78Kb(7, 64) == 96 && a78Kb(7, 128) == 256 && a78Kb(7, 16) == 0 && a78Kb(7, 144) == 0);
  CHECK(a78Std(16) == 16 && a78Std(17) == 32 && a78Std(32) == 32 && a78Std(33) == 48 && a78Std(64) == 48);
  // Atari 8 bits e Lynx (D210)
  CHECK(oscr::atari8::sizeIndex(8) == 0 && oscr::atari8::sizeIndex(40) == 3 && oscr::atari8::sizeIndex(128) == 5 && oscr::atari8::sizeIndex(24) == oscr::atari8::kBad);
  CHECK(oscr::atari8::totalKb(0, 32) == 32 && oscr::atari8::totalKb(0, 12) == 0 && oscr::atari8::totalKb(1, 0) == 8 && oscr::atari8::totalKb(1, 99) == 8 && oscr::atari8::totalKb(2, 8) == 0);
  CHECK(oscr::lynx::totalBytes(512) == 64 + 131072 && oscr::lynx::totalBytes(1024) == 64 + 262144 && oscr::lynx::totalBytes(2048) == 64 + 524288 && oscr::lynx::totalBytes(0) == 0 && oscr::lynx::totalBytes(256) == 0);
  // Atari Jaguar (D211)
  CHECK(oscr::jag::sizeIndex(1024) == 0 && oscr::jag::sizeIndex(2048) == 1 && oscr::jag::sizeIndex(4096) == 2 && oscr::jag::sizeIndex(0) == oscr::jag::kBad && oscr::jag::sizeIndex(512) == oscr::jag::kBad && oscr::jag::sizeIndex(6144) == oscr::jag::kBad);
  CHECK(oscr::jag::saveBytes(0) == 128 && oscr::jag::saveBytes(1) == 256 && oscr::jag::saveBytes(2) == 512 && oscr::jag::saveBytes(3) == 1024 && oscr::jag::saveBytes(4) == 2048 && oscr::jag::saveBytes(5) == 131072 && oscr::jag::saveBytes(6) == 0);
  printf("%d verificacoes do Atari 2600, 5200, 7800, 8 bits, Lynx e Jaguar, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
