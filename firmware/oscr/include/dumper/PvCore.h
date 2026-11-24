// SPDX-License-Identifier: GPL-3.0-or-later
// Casio PV-1000 (F-20, D219): 5 V, ROM do cartucho no barramento do slot SNES (adaptador de 36 pinos; pinagem em src/cores/CasioPV1000.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo CasioPV1000.cpp: tamanho em KB -> índice da tabela `PV1000` do núcleo (a leitura é o `readROM`
// do OSCR) e classificação do que o slot devolveu. Código puro: testado no PC em pc-tests/test_pv.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace pv
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (a ROM do PV-1000 não tem assinatura nem cabeçalho)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint16_t kBase = 0x0000;     ///< as duas janelas (8 KB com /CS1, 16 KB com /CS2) começam em $0000; a sondagem lê daí
  constexpr uint8_t kBadIndex = 0xFF;

  /// KB informado pelo PC -> índice da tabela `PV1000` do núcleo {8, 16} (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    return kb == 8 ? 0 : kb == 16 ? 1 : kBadIndex;
  }

  /// `sample` são `n` bytes lidos a partir de $0000. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do Pyuuta, Arcadia e NES).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::pv
