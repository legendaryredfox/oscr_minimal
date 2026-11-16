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

  /// Gameshark (2 chips SST 29LE010, AT29LV010A, SST 29EE010 ou SST 28LF040) e Xplorer 64 (2 x SST 29LE010): a flash do próprio acessório, não de um cartucho de jogo.
  constexpr uint16_t kGameshark = 2, kXplorer = 3;

  /// Confere o chip e o tamanho do arquivo (repro: múltiplo de 128 KB, até 64 MB; Gameshark: múltiplo de 16 KB, até 1 MB; Xplorer 64: exatamente 256 KB), sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint16_t chip, uint32_t sizeBytes);

  /// Com o cartucho ligado: lê o ID (E_FLASH se desconhecido), confere se a ROM cabe (E_ARGUMENTO) e apaga o que ela ocupa; sem apagar tudo (blankcheck): E_FLASH. 0 = ok.
  uint16_t prepare(uint16_t chip, uint32_t sizeBytes);

  /// Backup (leitura da flash do Gameshark ou do Xplorer 64 para o fluxo), com o OSCR `backupGameshark` ou `backupXplorer`. `chip` = kGameshark ou kXplorer. Liga e desliga o cartucho. 0 = ok; E_FLASH se o ID não é conhecido.
  uint16_t backup(uint16_t chip);

  /// Só identifica o acessório (sem ler nem apagar): 0 = ok, E_FLASH se o ID não é conhecido. Usado para recusar o backup antes de abrir o fluxo.
  uint16_t probe(uint16_t chip);

  /// Programa o chip com a função do OSCR do chip identificado. Os dados saem do "arquivo" do OSCR (`sharedFile`), que o chamador ligou ao fluxo. 0 = ok.
  uint16_t program(uint16_t chip, uint32_t sizeBytes);
}
