// SPDX-License-Identifier: GPL-3.0-or-later
// Interno do backend dos cartuchos: o que os arquivos oscr_carts_*.cpp compartilham.
#pragma once
#include <string.h>

#include "oscr_carts.h"

#if defined(__AVR__)
#include <avr/pgmspace.h>
#else
#define PROGMEM
#define pgm_read_word(p) (*(p))
#endif

namespace oscr {

static inline void copy_ascii(char* dst, const uint8_t* src, uint8_t n) {
  uint8_t o = 0;
  for (uint8_t i = 0; i < n && o < 32; i++) dst[o++] = (src[i] >= 0x20 && src[i] < 0x7F) ? char(src[i]) : ' ';
  while (o > 0 && dst[o - 1] == ' ') o--;   // tira espaços finais
  dst[o] = 0;
}

}  // namespace oscr
