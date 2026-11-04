// SPDX-License-Identifier: GPL-3.0-or-later
// Programador de flash genérico (sistema 7): ler, apagar, identificar e gravar flash e EPROM fora de cartucho de console. Menus de Flash.cpp do OSCR.
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::FlashProg
{
  /// Campo `chip` (u16, parte baixa) do programador genérico.
  enum : uint8_t
  {
    k8Adapter = 1,      ///< flash de 8 bits no adaptador de flash (`mapping` 0): menu "Flash Adapter" do OSCR
    k8Plcc32 = 2,       ///< flash de 8 bits PLCC32 no adaptador de SNES (`mapping` 3): menu "PLCC32 to SNES"
    k16 = 3,            ///< flash de 16 bits (Flash16): 29F1601, 29LV640 e outros
    kEprom = 4,         ///< EPROM 27C322 de 4 MB (16 bits)
  };

  /// `prg_kb` = tamanho do chip em KB (8 bits e 16 bits). `chr_kb` = tipo do flash de 8 bits (o mesmo campo do modo genérico do SnesFlash.h; 0 = não informado).
  /// Confere os campos e (se `sizeBytes` > 0) o tamanho do arquivo, sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes);

  /// Identifica o chip. `text` recebe até 31 caracteres para o DETECT. Devolve 0 se há chip (ou EPROM), 1 se o ID é 0000 ou FFFF em tudo.
  uint8_t detect(uint16_t chip, uint16_t prgKb, uint16_t chrKb, char * text, uint32_t & sizeBytes);

  /// Lê o chip inteiro para o fluxo (o chamador liga o `sharedFile` ao fluxo de saída).
  uint16_t read(uint16_t chip, uint16_t prgKb);

  /// Com o chip ligado: identifica (E_FLASH se não responde) e apaga. No EPROM confere que está em branco. 0 = ok. Também serve de ERASE.
  uint16_t prepare(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes);

  /// Grava o que vem do "arquivo" do OSCR (`sharedFile`, ligado ao fluxo pelo chamador). 0 = ok.
  uint16_t program(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes, oscr::StreamSource & in);
}
