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

// Atari 5200 e Atari 7800 (F-20, D209): 5 V, mesmo slot SNES. Como no 2600, o cartucho não diz o mapper nem o tamanho: o PC manda `mapper` (id do
// `a5200-mappers` / `a7800-mappers` do OSCR) e `prg_kb`. Os tamanhos saem do `readROM` de cada núcleo (src/cores/Atari5200.cpp e Atari7800.cpp) e as
// faixas aceitas de `prg_kb` saem das tabelas `a5200mapsize` e `a7800mapsize` do OSCR legado (vendor/oscr/legacy/Cart_Reader).
namespace oscr { namespace atari
{
  /// 5200. Mapper 0: 4, 8, 16 ou 32 KB (o `prg_kb`); 1: dois chips de 16 KB; 2: Bounty Bob Strikes Back, 40 KB. Devolve os KB que o `readROM` lê, 0 se inválido.
  inline uint16_t a52Kb(uint16_t mapper, uint16_t kb)
  {
    switch (mapper)
    {
      case 0: return (kb == 4 || kb == 8 || kb == 16 || kb == 32) ? kb : 0;
      case 1: return 16;
      case 2: return 40;
      default: return 0;
    }
  }

  /// KB que o `readStandard` do 7800 lê para o `romSize` dado (16, 32 ou 48).
  inline uint16_t a78Std(uint16_t kb) { return kb > 32 ? 48 : (kb > 16 ? 32 : 16); }

  /// 7800. Mapper 0: 16, 32 ou 48 KB; 1: SuperGame 128 KB; 2: 144 KB; 3: F-18 Hornet 64 KB; 4: Double Dragon/Rampage 128 KB; 5 e 6: 64 KB;
  /// 7: bankset (o `readROM` lê duas vezes, com HALT em 1 e em 0; `prg_kb` de 32, 48, 64 ou 128: acima de 64 lê o SuperGame de 128 KB duas vezes, senão o padrão duas vezes);
  /// 8: Crystal Quest/Bounty Bob 144 KB. Devolve os KB totais, 0 se inválido.
  inline uint16_t a78Kb(uint16_t mapper, uint16_t kb)
  {
    switch (mapper)
    {
      case 0: return (kb == 16 || kb == 32 || kb == 48) ? kb : 0;
      case 1: return 128;
      case 2: return 144;
      case 3: return 64;
      case 4: return 128;
      case 5: case 6: return 64;
      case 7: return (kb == 32 || kb == 48 || kb == 64 || kb == 128) ? (kb > 64 ? 256 : 2 * a78Std(kb)) : 0;
      case 8: return 144;
      default: return 0;
    }
  }
} }  // namespace oscr::atari

// Atari 8 bits (400/800/XL/XE) e Atari Lynx (F-20, D210). 8 bits: adaptador de 30 pinos no slot SNES, 5 V; o campo `mapper` do protocolo é o slot (0 = esquerdo,
// 1 = direito) e `prg_kb` o tamanho (o cartucho não informa). Lynx: adaptador de 34 pinos, 5 V; o tamanho sai do próprio cartucho (`detectCart` acha o bloco).
namespace oscr { namespace atari8
{
  constexpr uint8_t kBad = 0xFF;
  /// Índice do tamanho na tabela `romSizes` do núcleo (8, 16, 32, 40, 64 e 128 KB), `kBad` se não existe.
  inline uint8_t sizeIndex(uint16_t kb)
  {
    switch (kb) { case 8: return 0; case 16: return 1; case 32: return 2; case 40: return 3; case 64: return 4; case 128: return 5; default: return kBad; }
  }
  /// KB que o `readROM` lê: o slot direito sempre 8 (o `prg_kb` é ignorado); no esquerdo o `prg_kb`. 0 se inválido.
  inline uint16_t totalKb(uint16_t slot, uint16_t kb)
  {
    if (slot > 1) return 0;
    if (slot == 1) return 8;
    return sizeIndex(kb) == kBad ? 0 : kb;
  }
} }  // namespace oscr::atari8

namespace oscr { namespace lynx
{
  constexpr uint32_t kHeader = 64;   // LYNX_HEADER_SIZE do núcleo
  /// Bytes que o `readROM` entrega para o bloco achado por `detectCart`: cabeçalho de 64 bytes e 256 blocos. 0 se o bloco não é 512, 1024 ou 2048.
  inline uint32_t totalBytes(uint16_t block)
  {
    return (block == 512 || block == 1024 || block == 2048) ? kHeader + 256UL * block : 0;
  }
} }  // namespace oscr::lynx

// Atari Jaguar (F-20, D211): só a leitura de ROM. O núcleo AtariJaguar.cpp lê 32 bits por vez (PF, PK, PL e PC) e gera o endereço com 74HC595 (PE3, PE4, PE5 e PG5);
// o cartucho não diz o tamanho: `prg_kb` = 1024, 2048 ou 4096 (o `romSize` do núcleo é o índice 0, 1 ou 2).
namespace oscr { namespace jag
{
  constexpr uint8_t kBad = 0xFF;
  /// Índice do tamanho no `romSize` do núcleo (1, 2 ou 4 MB), `kBad` se não existe.
  inline uint8_t sizeIndex(uint16_t kb) { return kb == 1024 ? 0 : (kb == 2048 ? 1 : (kb == 4096 ? 2 : kBad)); }
  /// Save (D212): `mapper` 0 a 4 = EEPROM 93C46/56/66/76/86 (128 a 2048 bytes, `eepSize` do núcleo), 5 = flash AT29C010 de 128 KB do Memory Track. 0 se inválido.
  inline uint32_t saveBytes(uint16_t m) { return m <= 4 ? (128UL << m) : (m == 5 ? 0x20000UL : 0); }
} }  // namespace oscr::jag

