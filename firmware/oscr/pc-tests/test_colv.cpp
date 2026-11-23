// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/ColvCore.h (ColecoVision, F-20, D201): tabela de tamanhos e classificação do que o slot devolve.
// As mesmas regras estão nos simuladores (host/oscr_host/sim.py, SimDevice.kt): se mudarem, os testes de lá falham juntos.
#include <stdio.h>
#include <string.h>
#include "../include/dumper/ColvCore.h"

using namespace oscr::colv;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  // tabela do OSCR: 8, 12, 16, 20, 24 e 32 KB
  CHECK(sizeKb(0) == 8 && sizeKb(1) == 12 && sizeKb(2) == 16 && sizeKb(3) == 20 && sizeKb(4) == 24 && sizeKb(5) == 32);
  CHECK(sizeKb(6) == 0 && sizeKb(255) == 0);
  for (uint8_t i = 0; i < kSizeCount; i++) CHECK(sizeIndex(sizeKb(i)) == i);
  CHECK(sizeIndex(0) == kBadIndex && sizeIndex(4) == kBadIndex && sizeIndex(64) == kBadIndex && sizeIndex(1024) == kBadIndex);

  uint8_t s[32];
  // slot vazio: $FF (pull-up) ou $00 (barramento descarregado)
  memset(s, 0xFF, 32); CHECK(classify(s, 32) == kNoCart);
  memset(s, 0x00, 32); CHECK(classify(s, 32) == kNoCart);
  // valor único que não é $00 nem $FF não conta como vazio
  memset(s, 0x55, 32); CHECK(classify(s, 32) == kNoHeader);
  // assinaturas do console
  memset(s, 0x12, 32); s[0] = 0xAA; s[1] = 0x55; CHECK(classify(s, 32) == kOk);
  s[0] = 0x55; s[1] = 0xAA; CHECK(classify(s, 32) == kOk);
  // dados sem assinatura
  s[0] = 0x00; s[1] = 0x01; CHECK(classify(s, 32) == kNoHeader);
  // amostra curta demais
  CHECK(classify(s, 0) == kNoCart && classify(s, 1) == kNoCart);

  printf("%d verificacoes do ColecoVision, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
