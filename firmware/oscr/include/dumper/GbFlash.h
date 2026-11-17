// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em cartuchos repro de Game Boy com flash (WRITE_ROM, docs/referencia/protocolo.md). Menus "GB 29F/39SF Repro" e "GB CFI Repro" do OSCR (GameBoy.cpp).
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
    // Acessórios (F-17, D188): a flash do próprio acessório, não de um cartucho de jogo. Backup e conferência pela leitura do D186 (`DUMP_ROM` com `mapper` = 1, 2, 3).
    kPelican = 9,        ///< Pelican (Brainboys, MonsterBrains, Codebreaker): W29C020/29EE020 de 256 KB ou SST 28LF040 de 512 KB
    kMegaMem = 10,       ///< Datel Mega Memory Card: só o chip de dados SST 28LF040 (512 KB, os 32 bancos de 16 KB do `SaveData`)
    kGameShark = 11,     ///< Datel GameShark GBC: SST 39SF010 (128 KB)
    kLast = 11,
  };

  /// Confere chip e tamanho do arquivo (múltiplo de 16 KB, 32 KB a 4 MB; 32 KB no kOrangeFm; acessórios: Pelican 256 ou 512 KB, Mega Memory 512 KB, GameShark 128 KB), sem tocar no cartucho. 0 = ok; senão E_ARGUMENTO.
  uint16_t check(uint8_t chip, uint32_t sizeBytes);

  /// Com o cartucho ligado: lê o ID (E_FLASH se o chip não responde; no kCfi, se não responde ao CFI ou se a ROM não cabe) e apaga (menos no kCamSecond). 0 = ok.
  uint16_t prepare(uint8_t chip, uint32_t sizeBytes);

  /// Grava o que vem de [in] banco a banco. 0 = ok; E_CARTUCHO_IO se um byte não grava dentro do limite de tempo.
  uint16_t program(uint8_t chip, uint32_t sizeBytes, oscr::StreamSource & in);
}
