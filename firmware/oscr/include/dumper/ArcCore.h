// SPDX-License-Identifier: GPL-3.0-or-later
// Emerson Arcadia 2001 (F-20, D215): 5 V, ROM de 2 a 8 KB no barramento do slot SNES (adaptador de 30 pinos; pinagem em src/cores/Arcadia2001.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo Arcadia2001.cpp: tamanho em KB -> índice da tabela `romSizes` do núcleo (a leitura é o `readROM`
// do OSCR) e classificação do que o slot devolveu. Código puro: testado no PC em pc-tests/test_arc.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace arc
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (a ROM do Arcadia não tem assinatura nem cabeçalho)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint8_t kSizeCount = 4;
  constexpr uint8_t kBadIndex = 0xFF;

  /// Tamanhos do menu "Set ROM size" do OSCR (tabela `romSizes` do núcleo), em KB. O índice vai para `romSize`.
  inline uint16_t sizeKb(uint8_t index)
  {
    static const uint8_t kTab[kSizeCount] = { 2, 4, 6, 8 };
    return index < kSizeCount ? kTab[index] : 0;
  }

  /// KB informado pelo PC -> índice da tabela do núcleo (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    for (uint8_t i = 0; i < kSizeCount; i++) if (sizeKb(i) == kb) return i;
    return kBadIndex;
  }

  /// `sample` são `n` bytes lidos a partir de $0000. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do ColecoVision e do NES).
  /// Não há assinatura para conferir: o núcleo do OSCR também não detecta nada, o tamanho vem sempre do PC.
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::arc
