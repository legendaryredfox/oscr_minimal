// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos repro de Mega Drive com flash (WRITE_ROM, docs/protocolo.md). Fluxo do menu "Flash Repro" do OSCR (MegaDrive.cpp).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::MdFlash
{
  /// Valor do campo `mapper` do WRITE_ROM (aqui: o chip). O OSCR identifica o chip pelo ID: MX29F1610 (2 MB) ou S29GL064N (4 MB).
  enum : uint8_t { kAuto = 1 };

  /// Confere chip e tamanho do arquivo (par, até 4 MB), sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint8_t chip, uint32_t sizeBytes);

  /// Com o cartucho ligado: identifica o chip (E_FLASH se não for um dos dois), confere que a ROM cabe (E_ARGUMENTO) e apaga o chip inteiro. 0 = ok.
  uint16_t prepare(uint32_t sizeBytes);

  /// Programa o chip com `write29F1610` ou `write29GL` do OSCR. Os dados saem do "arquivo" do OSCR (`sharedFile`), que o chamador ligou ao fluxo. 0 = ok.
  uint16_t program();
}
