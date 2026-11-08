// SPDX-License-Identifier: GPL-3.0-or-later
// Testa include/dumper/SmsCore.h (Master System no slot direto, D137): slot vazio, cabeçalho "TMR SEGA", jogo sem cabeçalho,
// tamanho informado pelo PC. As mesmas regras estão no simulador do host (host/oscr_host/sim.py, SimDevice.kt): se mudarem, os testes de lá falham juntos.
#include <stdio.h>
#include <string.h>
#include <initializer_list>
#include "../include/dumper/SmsCore.h"

using namespace oscr::sms;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

int main() {
  uint8_t name[8], sample[32];

  // slot vazio: o barramento lê sempre o mesmo valor ($FF com pull-up, $00 com o barramento descarregado)
  memset(name, 0xFF, 8); memset(sample, 0xFF, 32);
  CHECK(classify(name, sample, 32, false) == kNoCart);
  memset(name, 0x00, 8); memset(sample, 0x00, 32);
  CHECK(classify(name, sample, 32, false) == kNoCart);
  // blocos com valores diferentes entre si ($FF no nome, $00 na amostra) não são slot vazio
  memset(name, 0xFF, 8); memset(sample, 0x00, 32);
  CHECK(classify(name, sample, 32, false) == kNoHeader);
  // valor único que não é $00 nem $FF (barramento flutuando em outro nível) não conta como vazio
  memset(name, 0x55, 8); memset(sample, 0x55, 32);
  CHECK(classify(name, sample, 32, false) == kNoHeader);

  // cabeçalho "TMR SEGA"
  memcpy(name, "TMR SEGA", 8);
  for (int i = 0; i < 32; i++) sample[i] = uint8_t(i * 7);
  CHECK(classify(name, sample, 32, false) == kOk);
  // "TMR SEGA" com a amostra toda $FF não é slot vazio (o nome decide)
  memset(sample, 0xFF, 32);
  CHECK(classify(name, sample, 32, false) == kOk);

  // sem cabeçalho (Mark III, SG-1000, jogo antigo)
  memcpy(name, "GAME   X", 8);
  CHECK(classify(name, sample, 32, false) == kNoHeader);
  // Fantasy Zone (J): o núcleo troca o nome por "TMR SEGA", e o DETECT passa essa informação
  CHECK(classify(name, sample, 32, true) == kOk);

  // tamanhos aceitos: os do menu "Set ROM size" do OSCR
  for (uint8_t c : {kSms, kGg}) {
    CHECK(sizeKbValid(c, 0));
    CHECK(sizeKbValid(c, 32) && sizeKbValid(c, 64) && sizeKbValid(c, 128) && sizeKbValid(c, 256) && sizeKbValid(c, 512) && sizeKbValid(c, 1024));
    CHECK(!sizeKbValid(c, 8) && !sizeKbValid(c, 16) && !sizeKbValid(c, 24) && !sizeKbValid(c, 48) && !sizeKbValid(c, 96) && !sizeKbValid(c, 2048));
  }
  // SG-1000: 8, 16, 24 e 32 KB, sem mapeador
  CHECK(sizeKbValid(kSg, 0) && sizeKbValid(kSg, 8) && sizeKbValid(kSg, 16) && sizeKbValid(kSg, 24) && sizeKbValid(kSg, 32));
  CHECK(!sizeKbValid(kSg, 64) && !sizeKbValid(kSg, 48) && !sizeKbValid(kSg, 1024));

  // adaptador pedido pelo PC -> SMSMode do núcleo (ordem do enum do OSCR: Retrode, GGRetrode, Retron, GGRetron, Raphnet, SG1000Raphnet)
  CHECK(mode(kSms, 0) == kSmsRaphnet && mode(kSms, 1) == kSmsRetrode && mode(kSms, 2) == kSmsRetron && mode(kSms, 3) == kBadMode);
  CHECK(mode(kGg, 0) == kGgRetron && mode(kGg, 1) == kGgRetrode && mode(kGg, 2) == kBadMode);
  CHECK(mode(kSg, 0) == kSg1000Raphnet && mode(kSg, 1) == kBadMode);
  CHECK(mode(9, 0) == kBadMode);
  CHECK(kSmsRetrode == 0 && kGgRetrode == 1 && kSmsRetron == 2 && kGgRetron == 3 && kSmsRaphnet == 4 && kSg1000Raphnet == 5);

  // tamanho final: o do PC vale sempre; sem ele só o cabeçalho serve
  CHECK(romBytes(kOk, 262144, 0) == 262144);
  CHECK(romBytes(kOk, 262144, 128) == 131072);
  CHECK(romBytes(kNoHeader, 49152, 0) == 0);
  CHECK(romBytes(kNoHeader, 49152, 512) == 524288);
  CHECK(romBytes(kOk, 0, 0) == 0);

  CHECK(kSramBytes == 32768);
  CHECK(kMaxRomKb == 1024);

  printf("test_sms: %d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
