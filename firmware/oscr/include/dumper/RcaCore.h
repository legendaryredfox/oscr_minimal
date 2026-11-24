// SPDX-License-Identifier: GPL-3.0-or-later
// RCA Studio II (F-20, D216): 5 V, ROM do cartucho no barramento do slot SNES (adaptador de 22 pinos; pinagem em src/cores/RCAStudio2.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo RCAStudio2.cpp: tamanho em KB -> índice da tabela `romSizes` do núcleo (a leitura é o `readROM`
// do OSCR) e classificação do que o slot devolveu. Código puro: testado no PC em pc-tests/test_rca.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace rca
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (a ROM do Studio II não tem assinatura nem cabeçalho)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint16_t kBase = 0x0400;     ///< a ROM começa em $0400; a sondagem lê daí
  constexpr uint8_t kBadIndex = 0xFF;

  /// Índice da tabela `romSizes` do núcleo oferecido ao PC. O núcleo tem dois índices ({1, 2} no menu), mas o `readROM` lê $0400-$05FF no 0 (512 bytes)
  /// e $0400-$07FF no 1 (1 KB): o menu do OSCR rotula 1 e 2 e lê 512 B e 1 KB. Só o índice 1 (1 KB, o tamanho que o PC informa em KB) é oferecido.
  constexpr uint8_t kIndex1Kb = 1;

  /// KB informado pelo PC -> índice da tabela do núcleo (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    return kb == 1 ? kIndex1Kb : kBadIndex;
  }

  /// `sample` são `n` bytes lidos a partir de $0400. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do Arcadia, ColecoVision e NES).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::rca
