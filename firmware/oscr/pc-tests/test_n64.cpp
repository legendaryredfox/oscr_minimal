// SPDX-License-Identifier: GPL-3.0-or-later
// Regras do N64 do fork (D158): include/dumper/N64Core.h. Sem hardware.
#include <stdio.h>
#include "../include/dumper/N64Core.h"

static int checks = 0, failures = 0;
#define CHECK(c) do { checks++; if (!(c)) { failures++; printf("FALHOU %s:%d: %s\n", __FILE__, __LINE__, #c); } } while (0)

int main()
{
  using namespace oscr::n64;
  uint8_t h[64];
  memset(h, 0xFF, sizeof h); CHECK(classify(h, 64) == kNoCart);
  memset(h, 0x00, sizeof h); CHECK(classify(h, 64) == kNoCart);
  memset(h, 0x5A, sizeof h); CHECK(classify(h, 64) == kBadHeader);            // valor único mas não é $00 nem $FF
  h[0] = 0x80; h[1] = 0x37; h[2] = 0x12; h[3] = 0x40; CHECK(classify(h, 64) == kOk);
  h[0] = 0x37; h[1] = 0x80; h[2] = 0x40; h[3] = 0x12; CHECK(classify(h, 64) == kBadHeader);   // v64 (bytes trocados): o barramento nunca entrega essa ordem
  memset(h, 0x00, sizeof h); h[10] = 1; CHECK(classify(h, 64) == kBadHeader);  // contato sujo: quase tudo $00

  CHECK(saveBytes(kSram) == 32768 && saveBytes(kSram768) == 98304 && saveBytes(kFlash) == 131072);
  CHECK(saveBytes(kEeprom4k) == 512 && saveBytes(kEeprom16k) == 2048 && saveBytes(kNone) == 0 && saveBytes(3) == 0);
  CHECK(eepromPages(kEeprom4k) == 64 && eepromPages(kEeprom16k) == 256 && eepromPages(kSram) == 0);
  CHECK(eepromPages(kEeprom4k) * 8 == saveBytes(kEeprom4k) && eepromPages(kEeprom16k) * 8 == saveBytes(kEeprom16k));
  CHECK(isEeprom(kEeprom4k) && isEeprom(kEeprom16k) && !isEeprom(kSram) && !isEeprom(kFlash) && !isEeprom(kNone));
  CHECK(saveTypeValid(0) && saveTypeValid(1) && saveTypeValid(2) && saveTypeValid(4) && saveTypeValid(5) && saveTypeValid(6));
  CHECK(!saveTypeValid(3) && !saveTypeValid(7) && !saveTypeValid(255));
  CHECK(romMbValid(1) && romMbValid(8) && romMbValid(64) && !romMbValid(0) && !romMbValid(65) && !romMbValid(128));

  char n[32];
  formatName(n, sizeof n, 0x3B941695UL, "NSME", "SUPER MARIO 64");
  CHECK(strcmp(n, "3B941695 NSME SUPER MARIO 64") == 0);
  formatName(n, sizeof n, 0x0000000AUL, "N\x01" "AB", "A VERY LONG TITLE OF 20CH");           // id com caractere de controle vira '?'; título cortado em 31
  CHECK(strcmp(n, "0000000A N?AB A VERY LONG TITLE") == 0 && strlen(n) == 31);
  formatName(n, 12, 0xFFFFFFFFUL, "ABCD", "X");                                              // buffer pequeno: sempre termina em zero
  CHECK(strlen(n) == 11);

  printf("test_n64: %d verificações, %d falhas\n", checks, failures);
  return failures ? 1 : 0;
}
