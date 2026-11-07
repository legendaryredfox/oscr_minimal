// SPDX-License-Identifier: GPL-3.0-or-later
// Testes de include/dumper/PowerCore.h no PC: espera da descarga e tentativas com ciclo de energia (SA-1).
#include <stdio.h>

#include "../include/dumper/PowerCore.h"

static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

using namespace oscr::power;

static void test_discharge() {
  uint32_t t = 0, delays = 0;
  auto now = [&] { return t; };
  auto delay_ms = [&](uint32_t ms) { t += ms; delays += ms; };
  // sem sensor: espera tudo
  CHECK(wait_discharge(false, 500, 2000, [] { return false; }, delay_ms, now) == 2000 && delays == 2000);
  // com sensor: sai quando o rail cai (aos 85 ms, em passos de 5 ms)
  t = 0; delays = 0;
  uint32_t el = wait_discharge(true, 500, 2000, [&] { return t >= 85; }, delay_ms, now);
  CHECK(el == 85 && delays == 85);
  // com sensor que nunca cai: desiste em 500 ms
  t = 0; delays = 0;
  el = wait_discharge(true, 500, 2000, [] { return false; }, delay_ms, now);
  CHECK(el >= 500 && el < 510);
  // rail já baixo: não espera nada
  t = 0; delays = 0;
  CHECK(wait_discharge(true, 500, 2000, [] { return true; }, delay_ms, now) == 0 && delays == 0);
}

static void test_retry() {
  int attempts = 0, cycles = 0; bool ok = false;
  // dá certo na 4ª tentativa com limite 5: 3 ciclos
  uint8_t n = retry_with_cycle(5, [&] { return ++attempts == 4; }, [&] { cycles++; }, ok);
  CHECK(n == 4 && ok && cycles == 3);
  // nunca dá certo, limite 3: 3 tentativas, 2 ciclos, ok falso
  attempts = 0; cycles = 0;
  n = retry_with_cycle(3, [&] { attempts++; return false; }, [&] { cycles++; }, ok);
  CHECK(n == 3 && !ok && attempts == 3 && cycles == 2);
  // dá certo de primeira: nenhum ciclo
  attempts = 0; cycles = 0;
  n = retry_with_cycle(3, [&] { attempts++; return true; }, [&] { cycles++; }, ok);
  CHECK(n == 1 && ok && cycles == 0);
  // sem ciclo de energia (limite 1): uma tentativa, sem ciclo
  attempts = 0; cycles = 0;
  n = retry_with_cycle(1, [&] { attempts++; return false; }, [&] { cycles++; }, ok);
  CHECK(n == 1 && !ok && cycles == 0);
  // a ordem é tentativa, ciclo, tentativa
  int order = 0; bool in_order = true;
  retry_with_cycle(2, [&] { in_order = in_order && (order == 0 || order == 2); order++; return false; }, [&] { in_order = in_order && order == 1; order++; }, ok);
  CHECK(in_order);
}

int main() {
  test_discharge();
  test_retry();
  printf("%d verificações do PowerCore, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
