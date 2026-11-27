// SPDX-License-Identifier: GPL-3.0-or-later
// MSX (F-20, D230): 5 V, adaptador de 50 pinos no slot SNES (pinagem no cabeçalho de src/cores/MSX.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo: o mapper e os tamanhos que o PC informa viram os índices `msxmapper`,
// `romSize` e `sramSize` do núcleo (o menu "Set Mapper" do OSCR lê a tabela de um arquivo do cartão SD, que aqui não existe),
// o tamanho do arquivo e a classificação do que o slot devolveu. O núcleo lê a ROM e lê e grava a SRAM (readROM, readRAM, writeRAM).
// Código puro: testado no PC em pc-tests/test_msx.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace msx
{
  enum : uint8_t
  {
    kOk = 0,           ///< há dados no barramento (o fork não exige o cabeçalho "AB": nem todo mapper mostra o banco 0 ao ligar)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint8_t kBadIndex = 0xFF;
  constexpr uint8_t kMapperCount = 15;   ///< mappers 0 a 14 do núcleo (`switch (msxmapper)` do `readROM`)
  constexpr uint8_t kRType = 12;         ///< R-Type: o `readROM` lê 24 bancos de 16 KB (384 KB) e ignora `romSize`
  constexpr uint8_t kPac = 11;          ///< PAC e FM-PAC: o `readROM` lê sempre 4 bancos de 16 KB (64 KB) e ignora `romSize`
  constexpr uint8_t kKoei = 7;           ///< Koei: com `sramSize` > 2 o núcleo lê e grava 32 KB (o índice 3, 16 KB, também daria 32 KB)
  constexpr uint16_t kRTypeKb = 384;

  /// Tabela `romSizes` do núcleo, em KB (o índice vai para `romSize`).
  inline uint16_t romKb(uint8_t index)
  {
    static const uint16_t kTab[9] = { 0, 8, 16, 32, 64, 128, 256, 512, 1024 };
    return index < 9 ? kTab[index] : 0;
  }

  /// Tabela `ramSizes` do núcleo, em KB (o índice vai para `sramSize`).
  inline uint8_t ramKb(uint8_t index)
  {
    static const uint8_t kTab[5] = { 0, 2, 8, 16, 32 };
    return index < 5 ? kTab[index] : 0;
  }

  /// Faixas de índices de cada mapper: {ROM menor, ROM maior, RAM menor, RAM maior}. Copiadas de `msxmapsize[]` do OSCR legado
  /// (vendor/oscr/legacy/Cart_Reader/MSX.ino); o firmware novo lê a mesma tabela do arquivo `msx-mappers` do cartão SD.
  inline bool range(uint8_t mapper, uint8_t & romLo, uint8_t & romHi, uint8_t & ramLo, uint8_t & ramHi)
  {
    static const uint8_t kTab[kMapperCount][4] = {
      { 1, 4, 0, 0 },   //  0 sem mapper (8, 16, 32 ou 64 KB)
      { 4, 7, 0, 2 },   //  1 ASCII8: SRAM de 2 KB (Dires) ou 8 KB (Xanadu, Wizardry)
      { 4, 8, 0, 2 },   //  2 ASCII16: SRAM de 2 KB (Daisenryaku, Hydlide 2) ou 8 KB (A-Train)
      { 4, 4, 0, 0 },   //  3 Cross Blaim (64 KB)
      { 5, 5, 2, 2 },   //  4 Game Master 2 (128 KB, SRAM de 8 KB)
      { 8, 8, 3, 3 },   //  5 HAL Note (1024 KB, SRAM de 16 KB)
      { 4, 4, 0, 0 },   //  6 Harry Fox (64 KB)
      { 6, 8, 2, 4 },   //  7 Koei: SRAM de 8 KB (Nobunaga no Yabou - Zenkoku Ban) ou 32 KB (Sangokushi II)
      { 4, 8, 0, 0 },   //  8 Konami sem SCC
      { 5, 8, 0, 0 },   //  9 Konami com SCC
      { 4, 4, 0, 0 },   // 10 MSX-DOS2 (64 KB)
      { 0, 4, 2, 2 },   // 11 PAC (sem ROM) e FM-PAC (64 KB), SRAM de 8 KB
      { 7, 7, 0, 0 },   // 12 R-Type (384 KB)
      { 5, 5, 0, 0 },   // 13 Super Lode Runner (128 KB)
      { 2, 3, 0, 0 },   // 14 Hudson Soft Bee Pack (16 ou 32 KB)
    };
    if (mapper >= kMapperCount) return false;
    romLo = kTab[mapper][0]; romHi = kTab[mapper][1]; ramLo = kTab[mapper][2]; ramHi = kTab[mapper][3];
    return true;
  }

  /// Mapper que o núcleo conhece (0 a 14).
  inline bool validMapper(uint16_t mapper) { return mapper < kMapperCount; }

  /// O mapper tem SRAM (algum tamanho de save acima de zero).
  inline bool hasSave(uint16_t mapper)
  {
    uint8_t a, b, c, d;
    return mapper <= 0xFF && range(uint8_t(mapper), a, b, c, d) && d > 0;
  }

  /// Mapper e KB de ROM informados pelo PC -> índice `romSize` do núcleo (`kBadIndex` se a combinação não existe).
  /// 0 KB nunca vale (o menu do OSCR só lê a ROM com `romSize` acima de zero). R-Type: o PC informa os 384 KB reais (índice 7 da tabela);
  /// PAC/FM-PAC: só 64 KB, o que o núcleo lê.
  inline uint8_t romIndex(uint16_t mapper, uint16_t kb)
  {
    uint8_t lo, hi, rlo, rhi;
    if (mapper > 0xFF || !range(uint8_t(mapper), lo, hi, rlo, rhi) || kb == 0) return kBadIndex;
    if (mapper == kRType) return kb == kRTypeKb ? hi : kBadIndex;
    if (mapper == kPac) return kb == 64 ? hi : kBadIndex;     // o PAC sem ROM não tem o que ler; o FM-PAC tem 64 KB
    for (uint8_t i = lo; i <= hi; i++) if (i > 0 && romKb(i) == kb) return i;
    return kBadIndex;
  }

  /// Bytes que o `readROM` do núcleo grava (0 se a combinação não existe).
  inline uint32_t romBytes(uint16_t mapper, uint16_t kb)
  {
    return romIndex(mapper, kb) == kBadIndex ? 0 : uint32_t(kb) * 1024UL;
  }

  /// Mapper e KB de SRAM informados pelo PC -> índice `sramSize` do núcleo (`kBadIndex` se não existe). Koei aceita 8 ou 32 KB:
  /// o núcleo lê e grava 32 KB com qualquer índice acima de 2, então o índice 3 (16 KB) daria um arquivo maior que o pedido.
  inline uint8_t ramIndex(uint16_t mapper, uint16_t kb)
  {
    uint8_t lo, hi, rlo, rhi;
    if (mapper > 0xFF || !range(uint8_t(mapper), lo, hi, rlo, rhi) || kb == 0) return kBadIndex;
    if (mapper == kKoei && kb == 16) return kBadIndex;
    for (uint8_t i = rlo; i <= rhi; i++) if (i > 0 && ramKb(i) == kb) return i;
    return kBadIndex;
  }

  /// Bytes que o `readRAM` lê e o `writeRAM` consome (0 se a combinação não existe).
  inline uint32_t ramBytes(uint16_t mapper, uint16_t kb)
  {
    return ramIndex(mapper, kb) == kBadIndex ? 0 : uint32_t(kb) * 1024UL;
  }

  /// Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do NES e do Master System).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0x00 || sample[0] == 0xFF) ? kNoCart : kOk;
  }

  /// Cabeçalho de ROM do MSX ("AB" no início da página), só informativo no DETECT.
  inline bool hasHeader(uint8_t const * sample, uint8_t n)
  {
    return n >= 2 && sample[0] == 0x41 && sample[1] == 0x42;
  }
} }  // namespace oscr::msx
