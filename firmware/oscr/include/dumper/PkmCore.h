// SPDX-License-Identifier: GPL-3.0-or-later
// Pokémon Mini (F-20, D227): 3,3 V, ROM do cartucho no barramento do slot SNES (adaptador de 32 pinos; pinagem em src/cores/PokemonMini.cpp do OSCR).
// O cartucho trava o endereço sozinho: o `readData` do núcleo manda A10 a A20 com HALE (PH0) e depois A0 a A9 com LALE (PH4), pelas mesmas linhas.
// As regras que o fork acrescenta em volta do núcleo: tamanho fixo do arquivo e classificação do que o slot devolveu. A leitura é o `readROM` do OSCR.
// Código puro: testado no PC em pc-tests/test_pkm.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace pkm
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (o fork não confere assinatura)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint32_t kRomBytes = 0x80000UL;   ///< o `readROM` do OSCR lê sempre 512 KB (o núcleo: "ALL ROMS ARE 512K")
  /// Primeiro endereço que o console lê do cartucho ($0000 a $1FFF são a BIOS e a RAM do console, $2000 a $20FF os registradores): a sondagem lê daí.
  constexpr uint32_t kBase = 0x2100UL;

  /// `prg_kb` do PC: 0 (não informado) ou 512; outro valor não existe (o arquivo tem sempre 512 KB).
  inline bool sizeValid(uint16_t kb) { return kb == 0 || kb == 512; }

  /// `sample` são `n` bytes lidos a partir de `kBase`. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do Odyssey 2 e do Supervision).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::pkm
