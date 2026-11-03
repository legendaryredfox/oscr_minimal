// SPDX-License-Identifier: GPL-3.0-or-later
// Plano de gravação do flash CFI de SNES com 1, 2 ou 4 chips: quantos bytes do arquivo vão para qual chip, em que endereço do chip.
// É a regra do `adjustFileSizeOffset` e do `writeCFI` do OSCR (Flash.cpp), sem o arquivo: o PC manda os trechos na ordem dos segmentos.
// Código puro (sem hardware): testado no PC em pc-tests e espelhado em host/oscr_host/romimage.py (snes_plan) e RomImage.kt.
#pragma once
#include <stdint.h>

namespace OSCR::Dumper::SnesFlash
{
  /// Parte alta do campo `chip` do WRITE_ROM do SNES (a baixa é a fiação: 1 LoROM, 2 HiROM, 3 ExLoROM, 4 ExHiROM).
  enum : uint8_t
  {
    kLayout1x = 0,        ///< 1 chip de 2 ou 4 MB ("1x 2MB", "1x 4MB"); capacidade em `prg_kb`
    kLayout2x2 = 1,       ///< 2 chips de 2 MB ("2x 2MB")
    kLayout2x4 = 2,       ///< 2 chips de 4 MB ("2x 4MB", ROM de 6 a 8 MB, metade alta no chip 1)
    kLayout4x2 = 3,       ///< 4 chips de 2 MB ("4x 2MB", ROM de 6 a 8 MB)
    kLayout1x8 = 4,       ///< 1 chip de 8 MB ("1x 8MB", ROM de 6 ou 8 MB, metades trocadas)
    kGeneric = 0x10,      ///< menus "LoROM/HiROM (P0)" e "ExLoROM/ExHiROM (P1)": flash de 8 bits de tipo informado pelo PC
  };

  struct Seg
  {
    uint8_t chip;         ///< 1 a 4: qual chip (muda o `mapping` do OSCR, como o `nextCFI`)
    uint32_t addr;        ///< endereço dentro do chip onde começa o trecho
    uint32_t len;         ///< bytes; 0 = o chip só é apagado
  };

  constexpr uint32_t kMB = 1UL << 20;

  /// Tamanho de cada chip (bytes) de uma disposição. `capBytes` só vale em kLayout1x. 0 = disposição inválida.
  inline uint32_t chipBytes(uint8_t layout, uint32_t capBytes)
  {
    switch (layout)
    {
    case kLayout1x: return (capBytes == 2 * kMB || capBytes == 4 * kMB) ? capBytes : 0;
    case kLayout2x2: return 2 * kMB;
    case kLayout2x4: return 4 * kMB;
    case kLayout4x2: return 2 * kMB;
    case kLayout1x8: return 8 * kMB;
    }
    return 0;
  }

  /// Preenche `out` (até 4 segmentos) para uma ROM de `size` bytes e devolve quantos; 0 = tamanho ou disposição inválidos.
  /// Segmentos na ordem em que o PC manda os trechos. Chips citados com `len` 0 existem e são apagados.
  inline uint8_t plan(uint8_t layout, uint32_t size, uint32_t capBytes, Seg * out)
  {
    if (size == 0 || size % 512UL != 0) return 0;
    switch (layout)
    {
    case kLayout1x:
      if (chipBytes(layout, capBytes) == 0 || size > capBytes) return 0;
      out[0] = {1, 0, size};
      return 1;
    case kLayout2x2:
      if (size > 4 * kMB) return 0;
      out[0] = {1, 0, size < 2 * kMB ? size : 2 * kMB};
      out[1] = {2, 0, size > 2 * kMB ? size - 2 * kMB : 0};
      return 2;
    case kLayout2x4:                            // o OSCR recusa ROM menor que 6 MB em flash de 8 MB invertido
      if (size < 6 * kMB || size > 8 * kMB) return 0;
      out[0] = {1, 0, size - 4 * kMB};          // metade alta do arquivo
      out[1] = {2, 0, 4 * kMB};                 // metade baixa
      return 2;
    case kLayout4x2:
      if (size < 6 * kMB || size > 8 * kMB) return 0;
      out[0] = {1, 0, 2 * kMB};                 // arquivo 4 a 6 MB
      out[1] = {2, 0, size > 6 * kMB ? 2 * kMB : 0};   // arquivo 6 a 8 MB
      out[2] = {3, 0, 2 * kMB};                 // arquivo 0 a 2 MB
      out[3] = {4, 0, 2 * kMB};                 // arquivo 2 a 4 MB
      return 4;
    case kLayout1x8:                            // só 6 MB e 8 MB: em outros tamanhos o OSCR lê além do fim do arquivo
      if (size != 6 * kMB && size != 8 * kMB) return 0;
      out[0] = {1, 0, size - 4 * kMB};          // arquivo 4 MB em diante vai para o começo do chip
      out[1] = {1, 4 * kMB, 4 * kMB};           // arquivo 0 a 4 MB vai para a metade de cima
      return 2;
    }
    return 0;
  }

  /// Quantos chips a disposição tem (todos são apagados).
  inline uint8_t chipCount(uint8_t layout)
  {
    return layout == kLayout2x2 || layout == kLayout2x4 ? 2 : (layout == kLayout4x2 ? 4 : 1);
  }
}
