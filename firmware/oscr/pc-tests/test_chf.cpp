// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/ChfCore.h (Fairchild Channel F, F-20, D224): tamanhos, modos e a procura do cabeçalho do readROM do OSCR.
#include <stdio.h>
#include "../include/dumper/ChfCore.h"

using namespace oscr::chf;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

static uint8_t scan(uint8_t const * pre, int n, uint8_t fill) {
  Scanner s;
  for (int i = 0; i < n; i++) if (s.feed(pre[i])) return s.result();
  while (!s.feed(fill)) {}
  return s.result();
}

int main() {
  CHECK(sizeIndex(2) == 0 && sizeIndex(3) == 1 && sizeIndex(4) == 2 && sizeIndex(6) == 3);
  CHECK(sizeIndex(0) == kBadIndex && sizeIndex(1) == kBadIndex && sizeIndex(5) == kBadIndex && sizeIndex(8) == kBadIndex && sizeIndex(16) == kBadIndex);
  CHECK(modeValid(0) && modeValid(1) && !modeValid(2) && !modeValid(255));
  CHECK(fileBytes(0, 2) == 2048 && fileBytes(0, 3) == 3072 && fileBytes(0, 6) == 6144 && fileBytes(1, 2) == 16384 && fileBytes(1, 4) == 16384);
  CHECK(fileBytes(2, 2) == 0 && fileBytes(0, 5) == 0 && fileBytes(1, 0) == 0);
  CHECK(isStart2(0x08) && isStart2(0x2B) && isStart2(0xAA) && isStart2(0xBB) && !isStart2(0x55) && !isStart2(0x00));

  uint8_t h1[] = { 0x12, 0x34, 0x55, 0x2B }; CHECK(scan(h1, 4, 0x00) == kOk);
  uint8_t h2[] = { 0x55, 0x08 }; CHECK(scan(h2, 2, 0xFF) == kOk);
  uint8_t h3[] = { 0x55, 0x55, 0x2B }; CHECK(scan(h3, 3, 0x00) == kNoHeader);      // o segundo $55 foi consumido como "segundo byte": o readROM não o reexamina
  uint8_t h4[] = { 0x55, 0x55, 0x55, 0xAA }; CHECK(scan(h4, 4, 0x00) == kOk);
  uint8_t h5[] = { 0x55, 0x12 }; CHECK(scan(h5, 2, 0x00) == kNoHeader);
  CHECK(scan(nullptr, 0, 0xFF) == kNoCart && scan(nullptr, 0, 0x00) == kNoCart);
  CHECK(scan(nullptr, 0, 0x37) == kNoHeader);

  Scanner s; uint16_t n = 0; while (!s.feed(0xFF)) n++;
  CHECK(s.reads == kScan && n + 1 == kScan);
  printf("%d verificacoes do Channel F, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
