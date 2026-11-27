// SPDX-License-Identifier: GPL-3.0-or-later
// Magnavox Odyssey 2 / Philips Videopac (F-20, D226): 5 V, ROM do cartucho no barramento do slot SNES (adaptador de 30 pinos em duas fileiras;
// pinagem em src/cores/Odyssey2.cpp do OSCR). As regras que o fork acrescenta em volta do núcleo: tamanho em KB -> índice da tabela `romSizes`
// do núcleo, o mapper do OSCR (`ody2mapper`: 0 = A10 sem ligação, 1 = A10 ligado), tamanho do arquivo e a classificação do que o slot devolveu.
// A leitura é o `readROM` do OSCR. Código puro: testado no PC em pc-tests/test_ody.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace ody
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (o fork não confere assinatura)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  /// Campo `mapper`, igual ao `ody2mapper` do núcleo (e ao mapper da base do OSCR): 0 = cartucho comum (A10 sem ligação; 2, 4 ou 8 KB em janelas
  /// de 2 KB, 12 e 16 KB trocando de banco), 1 = A10 ligado (Videopac 31 Musician e 40 4 in 1 Row: 4 KB contínuos de $0000).
  enum : uint8_t { kMapperStd = 0, kMapperA10 = 1 };

  constexpr uint16_t kBase = 0x0400;     ///< primeira janela que o `readROM` lê nos cartuchos comuns (e que existe também nos de A10 ligado); a sondagem lê daí
  constexpr uint8_t kBadIndex = 0xFF;

  /// KB informado pelo PC -> índice da tabela `romSizes` do núcleo {2, 4, 8, 12, 16} (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    return kb == 2 ? 0 : kb == 4 ? 1 : kb == 8 ? 2 : kb == 12 ? 3 : kb == 16 ? 4 : kBadIndex;
  }

  inline bool mapperValid(uint16_t m) { return m == kMapperStd || m == kMapperA10; }

  /// Combinação aceita: mapper 0 com qualquer tamanho da tabela; mapper 1 só com 4 KB (o `readROM` lê 4 KB nesse caso, qualquer que seja o tamanho).
  inline bool argsValid(uint16_t mapper, uint16_t kb)
  {
    if (!mapperValid(mapper) || sizeIndex(kb) == kBadIndex) return false;
    return mapper == kMapperStd || kb == 4;
  }

  /// Bytes que o `readROM` grava (0 se a combinação não vale).
  inline uint32_t fileBytes(uint16_t mapper, uint16_t kb)
  {
    return argsValid(mapper, kb) ? uint32_t(kb) * 0x400UL : 0;
  }

  /// `sample` são `n` bytes lidos a partir de `kBase`. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do Astrocade e do PV-1000).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::ody
