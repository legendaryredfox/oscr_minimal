// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos repro de SNES com flash (WRITE_ROM, docs/referencia/protocolo.md). Sequências do OSCR original (Flash.cpp, SNES.cpp).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"
#include "dumper/SnesPlan.h"

namespace OSCR::Dumper::SnesFlash
{
  /// Campo `chip` do WRITE_ROM: (disposição << 8) | fiação. Fiação: 1 LoROM, 2 HiROM, 3 ExLoROM (só kGeneric), 4 ExHiROM (só kGeneric), 5 adaptador de flash (`mapping` 0, só kGeneric: programador genérico) e 6 PLCC32 para SNES (`mapping` 3, só kGeneric).
  constexpr uint16_t code(uint8_t layout, uint8_t wiring) { return uint16_t((layout << 8) | wiring); }
  inline bool isGeneric(uint16_t chip) { return uint8_t(chip >> 8) == kGeneric; }

  /// Campo `chr_kb` do modo kGeneric: tipo do flash (1 a 8, o `FlashType` do OSCR) | log2(setor em bytes) << 4 | log2(buffer em bytes) << 9.
  /// `prg_kb` é a capacidade do chip em KB. O OSCR achava isso no banco CRDB, que o fork não tem: o PC informa.

  /// Confere os campos contra o tamanho do arquivo, sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes);

  /// Com o cartucho ligado: identifica o chip (E_FLASH se não responde ou se não cabe a ROM) e apaga todos os chips. 0 = ok.
  uint16_t prepare(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes);

  /// Com o cartucho ligado: grava o que vem de [in]. No modo kGeneric as funções do OSCR leem o "arquivo" (o chamador liga o fluxo a ele). 0 = ok.
  uint16_t program(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes, oscr::StreamSource & in);
}
