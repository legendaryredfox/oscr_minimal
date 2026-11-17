// SPDX-License-Identifier: GPL-3.0-or-later
// Mega Drive: RAM de backup do Sega CD e mapeador Realtec (F-16, D179). A detecção é do OSCR (`getCartInfo` põe `bramSize` e `realtec`);
// aqui só o que o protocolo mostra ao PC. Os mesmos valores estão em docs/referencia/protocolo.md e nos simuladores.
#pragma once
#include <stdint.h>

namespace OSCR::Dumper::MdExtra
{
  /// `save_type` do DETECT do Mega Drive para o cartucho de RAM de backup do Sega CD (1 a 3 = SRAM, 4 = EEPROM serial; o OSCR não usa o 5).
  constexpr uint8_t kSaveBram = 5;
  /// Nome que o DETECT devolve para esse cartucho (o OSCR não tem cabeçalho de jogo nele).
  constexpr char kBramName[] = "Sega CD RAM";
  /// A RAM de backup de 128 KB (cartucho oficial) ou 512 KB (Ultra CD); o OSCR deduz o tamanho do byte baixo do primeiro word.
  inline bool bramSizeValid(uint32_t bytes) { return bytes == 0x20000UL || bytes == 0x80000UL; }
}
