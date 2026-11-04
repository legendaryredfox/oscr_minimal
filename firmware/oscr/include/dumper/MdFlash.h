// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos repro de Mega Drive com flash (WRITE_ROM, docs/protocolo.md). Fluxo do menu "Flash Repro" do OSCR (MegaDrive.cpp).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::MdFlash
{
  /// Valor do campo `mapper` do WRITE_ROM (aqui: o chip). O chip é identificado pelo ID (tabela em `MdFlashCore.h`): MX29F1610 e S29GL064N
  /// (funções do OSCR), chips AMD de 32 e 64 Mbit, MX29L3211 (5555h), Intel PA28F400 e SST39VF320x/640x.
  enum : uint8_t { kAuto = 1 };

  /// Confere chip e tamanho do arquivo (par, até 8 MB), sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint8_t chip, uint32_t sizeBytes);

  /// Com o cartucho ligado: identifica o chip, sem apagar nada. `text` (32 bytes, pode ser nulo) recebe "NOME FFDD" (fabricante e dispositivo em hexa);
  /// `sizeBytes` = capacidade do chip. 0 = chip da tabela; E_FLASH = ID desconhecido (o texto tem "?" e o ID lido).
  /// Atenção: a sondagem ESCREVE comandos de ID no cartucho (ignorados por ROM de máscara).
  uint16_t identify(char * text, uint32_t & sizeBytes);

  /// Com o cartucho ligado: identifica o chip (E_FLASH se não estiver na tabela), confere que a ROM cabe (E_ARGUMENTO) e apaga o que a ROM ocupa
  /// (chip inteiro nos dois chips do OSCR; setores ou blocos, por layout, nos demais). E_CARTUCHO_IO se o apagamento estourou o limite de tempo. 0 = ok.
  uint16_t prepare(uint32_t sizeBytes);

  /// Programa o chip: `write29F1610` ou `write29GL` do OSCR nos dois chips do OSCR; o núcleo `MdFlashCore.h` nos demais. Os dados saem do "arquivo"
  /// do OSCR (`sharedFile`), que o chamador ligou ao fluxo. E_CARTUCHO_IO se uma palavra não gravou dentro do limite de tempo. 0 = ok.
  uint16_t program();
}
