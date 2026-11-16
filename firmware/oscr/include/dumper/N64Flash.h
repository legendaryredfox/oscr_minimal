// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos repro de N64 com flash (WRITE_ROM, docs/referencia/protocolo.md). Fluxo do `flashRepro` do OSCR (N64.cpp).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::N64Flash
{
  /// Campo `chip` do WRITE_ROM do N64: 1 = flash repro (o firmware identifica o chip pelo ID: Spansion S29GL256N, S29GL128N, ST M29W128GL, Macronix MX29LV640,
  /// Intel 4400L0ZDQ0, Fujitsu MSP55LV100S e MSP55LV512, Intel 512M29EW). Chip que o OSCR não reconhece (o menu de configuração manual dele) não é aceito.
  constexpr uint16_t kRepro = 1;

  /// Confere o chip e o tamanho do arquivo (múltiplo de 128 KB, até 64 MB), sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint16_t chip, uint32_t sizeBytes);

  /// Com o cartucho ligado: lê o ID (E_FLASH se desconhecido), confere se a ROM cabe (E_ARGUMENTO) e apaga o que ela ocupa; sem apagar tudo (blankcheck): E_FLASH. 0 = ok.
  uint16_t prepare(uint16_t chip, uint32_t sizeBytes);

  /// Programa o chip com a função do OSCR do chip identificado. Os dados saem do "arquivo" do OSCR (`sharedFile`), que o chamador ligou ao fluxo. 0 = ok.
  uint16_t program(uint16_t chip, uint32_t sizeBytes);
}
