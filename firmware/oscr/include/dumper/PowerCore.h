// SPDX-License-Identifier: GPL-3.0-or-later
// Regras da chave de 5V dos slots sem hardware (D115, D119, D123): espera da descarga e tentativas com ciclo de energia
// (SA-1). Código puro, sem Arduino: testado no PC em pc-tests/test_power_core.cpp; o Dumper.cpp só liga os pinos e o tempo.
#pragma once
#include <stdint.h>

namespace oscr { namespace power {

/// Espera o rail cair depois de abrir o Q1. Com sensor (Q3 no D53): sai assim que `sense()` diz "rail baixo" ou no `with_sensor_ms`.
/// Sem sensor: espera `blind_ms` inteiros (sem o transistor de descarga o rail só cai pelo consumo). Devolve os ms esperados.
template <class Sense, class Delay, class Now>
uint32_t wait_discharge(bool has_sensor, uint32_t with_sensor_ms, uint32_t blind_ms, Sense sense, Delay delay_ms, Now now) {
  if (!has_sensor) { delay_ms(blind_ms); return blind_ms; }
  uint32_t t0 = now();
  for (;;) {
    uint32_t el = uint32_t(now() - t0);
    if (sense()) return el;
    if (el >= with_sensor_ms) return el;
    delay_ms(5);
  }
}

/// SA-1: roda `attempt()` (devolve true se leu o cabeçalho) até dar certo ou acabarem as `max_attempts`; entre uma e outra chama `cycle()`
/// (desliga, espera a descarga, liga). Devolve quantas tentativas fez; `ok` diz se a última deu certo. Sem ciclo de energia: `max_attempts` = 1.
template <class Attempt, class Cycle>
uint8_t retry_with_cycle(uint8_t max_attempts, Attempt attempt, Cycle cycle, bool& ok) {
  uint8_t n = 0;
  ok = false;
  while (n < max_attempts) {
    if (n > 0) cycle();
    n++;
    if (attempt()) { ok = true; break; }
  }
  return n;
}

}}  // namespace oscr::power
