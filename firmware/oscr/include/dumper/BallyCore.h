// SPDX-License-Identifier: GPL-3.0-or-later
// Bally Astrocade (F-20, D223): 5 V, ROM do cartucho no barramento do slot SNES (adaptador de 26 pinos; pinagem em src/cores/BallyAstrocade.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo BallyAstrocade.cpp: tamanho em KB -> índice da tabela `BALLY` do núcleo (a leitura é o `readROM`
// do OSCR) e classificação do que o slot devolveu. Código puro: testado no PC em pc-tests/test_bally.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace bally
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (o fork não confere assinatura)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint16_t kBase = 0x0000;     ///< o `readROM` lê $0000 em diante (A0 a A12 do cartucho); a sondagem lê daí
  constexpr uint8_t kBadIndex = 0xFF;

  /// KB informado pelo PC -> índice da tabela `BALLY` do núcleo {2, 4, 8} (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    return kb == 2 ? 0 : kb == 4 ? 1 : kb == 8 ? 2 : kBadIndex;
  }

  /// `sample` são `n` bytes lidos a partir de $0000. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do PV-1000, Pyuuta e Arcadia).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::bally
