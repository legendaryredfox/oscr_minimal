// SPDX-License-Identifier: GPL-3.0-or-later
// Regras puras do NES/Famicom no dumper (sem hardware): cartucho ausente (F-15, D173). Testado no PC em pc-tests/test_nes.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace nes {
  /// Vale `n` bytes iguais a `v`.
  inline bool allEqual(uint8_t const * p, uint8_t n, uint8_t v)
  {
    for (uint8_t i = 0; i < n; i++) if (p[i] != v) return false;
    return true;
  }

  /**
   * Cartucho ausente: o barramento de dados lê um único valor, $00 (descarregado) ou $FF (pull-up), em TODAS as janelas de PRG lidas.
   * Janelas usadas pelo `nesProbe`: $8000 (64 B), $A000 (16 B), $C000 (64 B) e $FFC0 (16 B, inclui os vetores NMI, RESET e IRQ).
   * Antes (D-anterior) eram só $8000 e $C000: um cartucho com bancos em branco nessas duas janelas, mas com o vetor RESET gravado, era dado como ausente.
   * Todas as janelas têm que ter o MESMO valor: um slot vazio não muda de valor de um endereço para outro, uma ROM vazia de flash ($FF) nunca tem vetor RESET $FFFF e
   * ainda assim cairia aqui, mas então não há o que ler. Nenhuma dessas regras foi vista em hardware.
   */
  inline bool cartAbsent(uint8_t const * w8000, uint8_t n8000, uint8_t const * wA000, uint8_t nA000,
                         uint8_t const * wC000, uint8_t nC000, uint8_t const * wFFC0, uint8_t nFFC0)
  {
    uint8_t v = w8000[0];
    if (v != 0x00 && v != 0xFF) return false;
    return allEqual(w8000, n8000, v) && allEqual(wA000, nA000, v) && allEqual(wC000, nC000, v) && allEqual(wFFC0, nFFC0, v);
  }
} }  // namespace oscr::nes
