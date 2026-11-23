// SPDX-License-Identifier: GPL-3.0-or-later
// Atari 2600 (F-20, D206): 5 V, ROM de 2 a 256 KB no barramento do slot SNES (adaptador de 24 pinos; pinagem em src/cores/Atari2600.cpp do OSCR).
// O núcleo Atari2600.cpp escolhe o método de leitura pelo id do mapper (os ids do banco `a2600-mappers` do OSCR, que fica no SD); aqui só ficam
// a lista de ids que o `readROM` do núcleo trata, o tamanho que cada um lê e a classificação do que o slot devolveu.
// Código puro: testado no PC em pc-tests/test_a26.cpp. Os tamanhos foram contados nos laços do `readROM`.
#pragma once
#include <stdint.h>

namespace oscr { namespace a26
{
  enum : uint8_t
  {
    kOk = 0,           ///< há dados no slot (o cartucho não tem cabeçalho: o mapper vem do PC)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint16_t kUnknown = 0xFFFF;   ///< id de mapper que o `readROM` não trata (cairia no `default:` e não leria nada)
  constexpr uint16_t kVariable = 0;       ///< E7: 8, 12 ou 16 KB, o núcleo descobre pelo conteúdo

  struct Map { uint16_t id; uint16_t kb; };

  /// Ids do `switch` de `readROM` e o tamanho em KB que cada um lê. Os de RAM extra (F4SC, F6SC, F8SC) leem o mesmo tamanho dos sem RAM.
  inline Map const * table(uint8_t & n)
  {
    static const Map kTab[] = {
      { 0x20, 2 },   { 0xC0, 2 },   { 0x40, 4 },   { 0x3F, 8 },   { 0xE0, 8 },   { 0xF8, 8 },   { 0x08, 8 },   { 0xF9, 8 },
      { 0xFE, 8 },   { 0x0A, 8 },   { 0xD0, 10 },  { 0xFA, 12 },  { 0xE7, kVariable }, { 0xF6, 16 }, { 0x06, 16 }, { 0x3E, 32 },
      { 0xF4, 32 },  { 0x04, 32 },  { 0xF0, 64 },  { 0x07, 64 },  { 0xDF, 128 }, { 0xBA, 128 }, { 0xBB, 256 },
    };
    n = sizeof kTab / sizeof kTab[0];
    return kTab;
  }

  /// Tamanho em KB lido pelo mapper `id`; `kVariable` (0) para o E7; `kUnknown` se o id não existe.
  inline uint16_t mapperKb(uint16_t id)
  {
    uint8_t n; Map const * t = table(n);
    for (uint8_t i = 0; i < n; i++) if (t[i].id == id) return t[i].kb;
    return kUnknown;
  }

  inline bool mapperValid(uint16_t id) { return mapperKb(id) != kUnknown; }

  /// `sample` são `n` bytes lidos a partir de $1000 (início da ROM no mapa do console). Slot vazio = um valor só, $00 ou $FF.
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::a26
