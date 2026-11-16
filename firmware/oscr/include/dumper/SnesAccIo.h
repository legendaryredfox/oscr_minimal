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
}
