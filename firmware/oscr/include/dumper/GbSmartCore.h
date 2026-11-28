// SPDX-License-Identifier: GPL-3.0-or-later
// GB Smart Card 32M (F-20, D249): o "Game Menu" do OSCR (`GameBoySmart::gameMenu`) pela serial. O cartucho vai no slot GBA com o adaptador GB, como o GB.
// A costura de Dumper.cpp chama o `getGames` do OSCR página a página até o jogo N, depois `remapStartBank` e o `checkCart`, `readROM`, `readSRAM` e
// `writeSRAM` do núcleo do GB, na ordem do menu. Aqui ficam as regras puras em volta disso. Código puro: testado no PC em pc-tests/test_gbs.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace gbs
{
  enum : uint8_t
  {
    kOk = 0,           ///< jogo N achado e o cabeçalho dele confere
    kNoCart = 1,       ///< slot vazio (o `checkCart` não achou cabeçalho)
    kBadHeader = 4,    ///< há dados, mas o checksum do cabeçalho do jogo não confere
    kPastEnd = 5,      ///< o cartucho tem menos jogos que N + 1
  };

  constexpr uint16_t kWhole = 0xFF;              ///< `mapper` = a flash inteira (o "Flash Menu > Read" do OSCR, `readFlash`)
  constexpr uint16_t kMaxGames = 127;            ///< 4 MB em blocos de 32 KB, menos o menu (bancos 0 e 1)
  constexpr uint8_t kMaxPages = 32;              ///< limite do laço de páginas (o OSCR mostra 6 jogos por página)
  constexpr uint32_t kFlashBytes = 4194304UL;    ///< 256 bancos de 16 KB

  /// `mapper` aceito: índice do jogo (0 = o primeiro depois do menu) ou `kWhole`.
  inline bool validIndex(uint16_t m) { return m < kMaxGames || m == kWhole; }

  /// Código de tamanho do cabeçalho do GB (`0x148`) válido para jogo: 0 a 8 (32 KB a 8 MB).
  inline bool validRomCode(uint8_t code) { return code <= 8; }

  /// O `getGames` do OSCR não para no fim da lista: depois do último jogo ele lê um banco apagado ($FF) e devolve uma entrada com
  /// tamanho `0xFF`. A costura trata a primeira entrada com tamanho inválido como o fim.
  inline bool isEnd(uint8_t romSizeCode) { return !validRomCode(romSizeCode); }

  /// Bytes da ROM pelo código do cabeçalho (0 se inválido).
  inline uint32_t romBytes(uint8_t code) { return validRomCode(code) ? (32768UL << code) : 0; }
} }  // namespace oscr::gbs
