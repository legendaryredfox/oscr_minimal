// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos de flash do NES (WRITE_ROM, docs/protocolo.md). Sequências do OSCR original (NES.cpp).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::NesFlash
{
  /// Valor do campo `mapper` do WRITE_ROM (aqui: o chip).
  enum : uint8_t
  {
    kNesMaker = 1,    ///< NES Maker, SST 39SF040 (mapper 30), PRG de até 512 KB, sem CHR-ROM
    kA29040B = 2,     ///< A29040B (mapper 0), PRG de 16 ou 32 KB e CHR de 0 ou 8 KB
  };

  /// Confere chip e tamanhos (KB) contra o tamanho do arquivo, sem tocar no cartucho. 0 = ok; senão o código de erro do protocolo (E_ARGUMENTO).
  uint16_t check(uint8_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes);

  /// Com o cartucho ligado: confere o ID do chip (E_FLASH se não for o esperado) e, no A29040B, apaga PRG e CHR. 0 = ok.
  uint16_t prepare(uint8_t chip, uint16_t prgKb, uint16_t chrKb);

  /// Com o cartucho ligado: programa o que vem de [in] (PRG e depois CHR) e confere cada byte, com limite de tempo. 0 = ok; E_CARTUCHO_IO se um byte não grava.
  uint16_t program(uint8_t chip, uint16_t prgKb, uint16_t chrKb, oscr::StreamSource & in);
}
