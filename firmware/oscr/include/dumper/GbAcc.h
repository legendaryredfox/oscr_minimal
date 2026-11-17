// SPDX-License-Identifier: GPL-3.0-or-later
// Game Boy: leitura de acessórios (F-17, D186). `DUMP_ROM` do GB com `mapper` 1 a 6 chama a função de leitura do OSCR do acessório, sem olhar o cabeçalho
// de jogo (os acessórios não têm o cabeçalho de cartucho comum). Só leitura: nenhuma das gravações (Pelican, Datel, GameShark, GB Memory, GB Smart) está ligada.
// O OSCR grava um arquivo por vez; aqui os arquivos vão seguidos no mesmo fluxo (o `open` e o `close` do StreamFile não mexem no fluxo).
#pragma once
#include <stdint.h>

namespace OSCR::Dumper::GbAcc
{
  enum : uint16_t { kNone = 0, kPelican = 1, kMegaMem = 2, kGameShark = 3, kGbMemory = 4, kGbMemoryMap = 5, kGbSmart = 6, kLast = 6 };

  inline bool valid(uint16_t a) { return a >= kPelican && a <= kLast; }

  /// Bytes que a leitura do OSCR entrega (0 = depende do chip: Pelican 256 KB com 29EE020/W29C020, 512 KB com SST 28LF040).
  inline uint32_t expectedBytes(uint16_t a)
  {
    switch (a)
    {
    case kMegaMem: return 16384UL + 32UL * 8192UL;          // ROM de 16 KB e depois 32 bancos de 8 KB de dados salvos (`SaveData`)
    case kGameShark: return 16UL * 8192UL;                  // SST 39SF010: 16 bancos de 8 KB (os 128 KB do chip, pela janela de 8 KB)
    case kGbMemory: return 32768UL + 62UL * 16384UL;        // banco 1 inteiro (32 KB) e os bancos 2 a 63 pela janela de 16 KB
    case kGbMemoryMap: return 128;                          // mapeamento escondido do GB Memory Module
    case kGbSmart: return 256UL * 16384UL;                  // 32 Mbit: 256 bancos de 16 KB
    default: return 0;
    }
  }
}
