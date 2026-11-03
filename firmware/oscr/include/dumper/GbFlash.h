// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos repro de Game Boy com flash (WRITE_ROM, docs/protocolo.md). Menus "GB 29F/39SF Repro" e "GB CFI Repro" do OSCR (GameBoy.cpp).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper::GbFlash
{
  /// Valor do campo `chip` do WRITE_ROM do GB. Os seis primeiros são os itens do menu "GB 29F/39SF Repro" (que chamam `GB::writeFlash(MBC, comandos, apagar)`).
  enum : uint8_t
  {
    kDiyMbc3 = 1,        ///< "DIY MBC3 (WR)": MBC3, comandos padrão, apaga
    kDiyMbc5 = 2,        ///< "DIY MBC5 (WR)": MBC5, comandos padrão, apaga
    kHdrMbc30 = 3,       ///< "HDR MBC30 (Audio)": MBC3, WE no pino de áudio, apaga
    kCamFirst = 4,       ///< "HDR GameBoy Cam", 1º jogo: MBC3, apaga (igual ao kDiyMbc3)
    kCamSecond = 5,      ///< "HDR GameBoy Cam", 2º jogo: MBC3, SEM apagar
    kOrangeFm = 6,       ///< "Orange FM (WR)": sem MBC, comandos do 39SF040, apaga; ROM de 32 KB
    kSst39Mbc5 = 7,      ///< "39SF MBC5 (Audio)": MBC5, comandos do 39SF040, WE no pino de áudio, apaga
    kCfi = 8,            ///< "GB CFI Repro": flash CFI (o OSCR identifica pelo CFI)
  };

  /// Confere chip e tamanho do arquivo (múltiplo de 16 KB, 32 KB a 4 MB; 32 KB no kOrangeFm), sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint8_t chip, uint32_t sizeBytes);

  /// Com o cartucho ligado: lê o ID (E_FLASH se o chip não responde; no kCfi, se não responde ao CFI ou se a ROM não cabe) e apaga (menos no kCamSecond). 0 = ok.
  uint16_t prepare(uint8_t chip, uint32_t sizeBytes);

  /// Grava o que vem de [in] banco a banco. 0 = ok; E_CARTUCHO_IO se um byte não grava dentro do limite de tempo.
  uint16_t program(uint8_t chip, uint32_t sizeBytes, oscr::StreamSource & in);
}
