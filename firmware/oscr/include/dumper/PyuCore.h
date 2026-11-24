// SPDX-License-Identifier: GPL-3.0-or-later
// Tomy Pyuuta (F-20, D217): 5 V, ROM do cartucho no barramento do slot SNES (adaptador de 36 pinos; pinagem em src/cores/TomyPyuuta.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo TomyPyuuta.cpp: tamanho em KB -> índice da tabela `romSizes` do núcleo (a leitura é o `readROM`
// do OSCR) e classificação do que o slot devolveu. Código puro: testado no PC em pc-tests/test_pyu.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace pyu
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (a ROM do Pyuuta não tem assinatura nem cabeçalho)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint16_t kBase = 0x8000;     ///< todo cartucho tem os primeiros 8 KB em $8000 (/CS0); a sondagem lê daí
  constexpr uint8_t kBadIndex = 0xFF;

  /// KB informado pelo PC -> índice da tabela `romSizes` do núcleo {8, 16, 32} (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    return kb == 8 ? 0 : kb == 16 ? 1 : kb == 32 ? 2 : kBadIndex;
  }

  /// `sample` são `n` bytes lidos a partir de $8000. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do Arcadia, ColecoVision e NES).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::pyu
