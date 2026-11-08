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

/// Seletor de tensão do cartucho (D138). Valores de `PowerInfo::volt`: 0 sem seletor (5 V fixo), 1 = 3,3 V, 2 = 5 V.
enum : uint8_t { kVoltNone = 0, kVolt3V3 = 1, kVolt5V = 2 };

/// Ação do POWER -> tensão pedida (0 = a ação não escolhe tensão).
inline uint8_t action_volt(uint8_t action) { return action == 3 ? kVolt3V3 : action == 4 ? kVolt5V : kVoltNone; }

/// Trocar de tensão com os slots ligados exige desligar antes (soltar os pinos, abrir o Q1 e esperar a descarga): nunca se muda a tensão "a quente".
inline bool needs_cycle(bool powered, uint8_t current, uint8_t wanted) { return powered && current != wanted; }

/// Depois de desligar, a tensão volta para o padrão (5 V, como nos flashcarts comuns de Mega Drive: o AMS1117 do cartucho precisa de ~4,5 V na entrada): o próximo POWER_ON sem tensão escolhida começa em 5 V. 3,3 V é opção explícita do usuário.
inline uint8_t after_off(bool has_selector) { return has_selector ? kVolt5V : kVoltNone; }

}}  // namespace oscr::power
