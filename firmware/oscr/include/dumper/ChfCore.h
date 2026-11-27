// SPDX-License-Identifier: GPL-3.0-or-later
// Fairchild Channel F (F-20, D224): 5 V, ROM do cartucho lida pelo protocolo ROMC do F8 (adaptador de 22 pinos no slot SNES; pinagem em
// src/cores/ChannelF.cpp do OSCR). As regras que o fork acrescenta em volta do núcleo: tamanho em KB -> índice da tabela `romSizes` do núcleo,
// modo de leitura (`readROM` ou `read16K` do OSCR), tamanho do arquivo e a procura do cabeçalho que a sondagem faz, idêntica à do `readROM`.
// Código puro: testado no PC em pc-tests/test_chf.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace chf
{
  enum : uint8_t
  {
    kOk = 0,           ///< achou o cabeçalho ($55 seguido de $08, $2B, $AA ou $BB), o mesmo que o `readROM` do OSCR procura
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
    kNoHeader = 4,     ///< há dados, mas o cabeçalho não apareceu nas leituras: o `readROM` não gravaria nada (o `read16K` ainda lê)
  };

  enum : uint8_t { kModeRom = 0, kModeRaw16K = 1 };    ///< campo `mapper`: 0 = `readROM` (pelo cabeçalho), 1 = `read16K` ("Read 16K" do menu do OSCR)

  constexpr uint16_t kScan = 0x4800;     ///< quantas leituras o `readROM` do núcleo faz procurando o cabeçalho
  constexpr uint8_t kBadIndex = 0xFF;

  /// KB informado pelo PC -> índice da tabela `romSizes` do núcleo {2, 3, 4, 6} (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    return kb == 2 ? 0 : kb == 3 ? 1 : kb == 4 ? 2 : kb == 6 ? 3 : kBadIndex;
  }

  inline bool modeValid(uint16_t mode) { return mode == kModeRom || mode == kModeRaw16K; }

  /// Bytes que o núcleo grava: o `readROM` grava o tamanho da tabela; o `read16K` grava sempre 32 blocos de 512 bytes.
  inline uint32_t fileBytes(uint16_t mode, uint16_t kb)
  {
    if (!modeValid(mode) || sizeIndex(kb) == kBadIndex) return 0;
    return mode == kModeRaw16K ? 0x4000UL : uint32_t(kb) * 0x400UL;
  }

  /// Segundo byte do cabeçalho que o `readROM` aceita depois do $55.
  inline bool isStart2(uint8_t b) { return b == 0x08 || b == 0x2B || b == 0xAA || b == 0xBB; }

  /// A procura do `readROM`, byte a byte: um $55 consome o byte seguinte; se esse não for um dos aceitos, a procura continua no próximo
  /// (o byte consumido não é reexaminado). Também anota se todos os bytes foram iguais, para separar slot vazio de cartucho sem cabeçalho.
  struct Scanner
  {
    uint16_t reads = 0;
    bool found = false, afterStart = false, same = true;
    uint8_t first = 0;

    /// Devolve true quando a procura acabou (achou o cabeçalho ou esgotou `kScan` leituras).
    bool feed(uint8_t b)
    {
      if (reads == 0) first = b; else if (b != first) same = false;
      reads++;
      if (afterStart) { afterStart = false; if (isStart2(b)) { found = true; return true; } }
      else if (b == 0x55) afterStart = true;
      return reads >= kScan && !afterStart;
    }

    uint8_t result() const
    {
      if (found) return kOk;
      if (same && (first == 0x00 || first == 0xFF)) return kNoCart;
      return kNoHeader;
    }
  };
} }  // namespace oscr::chf
