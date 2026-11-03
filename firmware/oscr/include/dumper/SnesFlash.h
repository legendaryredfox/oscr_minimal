// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos repro de SNES com flash CFI (WRITE_ROM, docs/protocolo.md). Sequências do OSCR original (Flash.cpp: writeCFI).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::SnesFlash
{
  /// Valor do campo `mapper` do WRITE_ROM (aqui: o chip, igual ao menu "CFI LoROM / CFI HiROM" do OSCR). `prg_kb` = capacidade do flash em KB.
  enum : uint8_t
  {
    kCfiLoRom = 1,    ///< flash CFI com a fiação de LoROM (`Flash::mapping = 1`)
    kCfiHiRom = 2,    ///< flash CFI com a fiação de HiROM (`Flash::mapping = 2`)
  };

  /// Capacidades aceitas (KB) de um chip só: 2 MB ou 4 MB (as opções "1x 2MB" e "1x 4MB" do OSCR).
  /// Confere chip, capacidade e tamanho do arquivo, sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint8_t chip, uint16_t capacityKb, uint32_t sizeBytes);

  /// Com o cartucho ligado: identifica o CFI (E_FLASH se não responde ou se o chip é menor que a capacidade pedida) e apaga o chip inteiro. 0 = ok.
  uint16_t prepare(uint8_t chip, uint16_t capacityKb);

  /// Com o cartucho ligado: programa o que vem de [in] a partir do endereço 0, com limite de tempo por byte. 0 = ok; E_CARTUCHO_IO se um byte não grava.
  uint16_t program(uint8_t chip, uint32_t sizeBytes, oscr::StreamSource & in);
}
