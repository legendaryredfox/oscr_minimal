// SPDX-License-Identifier: GPL-3.0-or-later
// Costura dos acessórios do SNES (F-10, D178) com os núcleos ST.cpp e GPC.cpp do OSCR.
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::SnesAcc
{
  /// Liga o adaptador e confere o cabeçalho "BANDAI SFC-ADX" do adaptador (banco 0) e do cartucho do slot. 0 = ok; E_SEM_CARTUCHO se faltar um dos dois.
  /// `bytes` recebe o tamanho (512 KB ou 1 MB) e `fileName` do OSCR o nome do cartucho (a última chamada de `getHeader` é a do slot).
  uint16_t probeSufami(bool slotB, uint32_t & bytes);

  /// Grava os 512 KB do GPC lendo o "arquivo" do OSCR (`sharedFile`, ligado ao fluxo pelo chamador). Mesma ordem do `writeRAM` do OSCR, sem a conferência (que relê o arquivo): o PC lê de volta.
  void writeGpc();

  /// BS-X (F-11, D187): confere o cartucho base pelo checksum `8B86` em `$00:FFDE` (a mesma conferência que o `writeFlash` do OSCR faz); 0 ou E_SEM_CARTUCHO.
  uint16_t probeBsx();
  /// Grava os 32 KB da SRAM do BS-X (bancos `$10` a `$17`, `$5000` a `$5FFF`) com o laço do `writeSRAM` do OSCR, lendo o "arquivo" do fluxo; sem a conferência (o PC lê de volta).
  void writeBsxSram();
  /// Leituras do SFM que o menu do OSCR fazia: jogo `idx` (troca o jogo e lê, como o `gameMenu`), flash inteira de 4 MB e mapeamento (512 bytes).
  void readSfmGame(uint8_t idx);
  void readSfmMap();
}
