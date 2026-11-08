// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos repro de GBA com flash (WRITE_ROM, docs/referencia/protocolo.md). Fluxo do `flashRepro` do OSCR (GameBoyAdvance.cpp).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::GbaFlash
{
  /// Campo `chip` do WRITE_ROM do GBA: (bloco << 8) | 1. O chip é identificado pelo ID (Intel 4000L0YBQ0, Intel 4400L0ZDQ0, MX29GL128E,
  /// MSP55LV128(N), PC28F256M29, M29W128GH e 369-in-1 F0088H0). O bloco (0 a 63, de 4 MB) só vale no 369-in-1 ("Write Offset" do OSCR).
  constexpr uint16_t code(uint8_t block) { return uint16_t((block << 8) | 1); }
  inline uint8_t blockOf(uint16_t chip) { return uint8_t(chip >> 8); }

  /// Confere o chip e o tamanho do arquivo (múltiplo de 1 KB, até 32 MB; no bloco 0 do 369-in-1, até 256 MB), sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint16_t chip, uint32_t sizeBytes);

  /// Com o cartucho ligado: lê o ID (E_FLASH se desconhecido), confere o bloco (E_ARGUMENTO se não é 369-in-1) e apaga o que a ROM ocupa. 0 = ok.
  uint16_t prepare(uint16_t chip, uint32_t sizeBytes);

  /// Programa o chip com a função do OSCR do chip identificado. Os dados saem do "arquivo" do OSCR (`sharedFile`), que o chamador ligou ao fluxo. 0 = ok.
  uint16_t program(uint16_t chip, uint32_t sizeBytes);
}
