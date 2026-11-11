// SPDX-License-Identifier: GPL-3.0-or-later
// Fork oscr_minimal: laço de comandos do protocolo serial ligado aos núcleos do OSCR (docs/referencia/fork-oscr.md).
#pragma once
#include "syslibinc.h"
#include "dumper/oscr_session.h"

namespace OSCR::Dumper
{
  /// Chamado no fim do `setup()`: abre a serial no baud do protocolo e prepara o laço.
  void setup();

  /// Chamado no `loop()`: atende no máximo um comando completo do PC.
  void loop();

  /// Fluxo ativo durante um comando (nulos fora dele). O `StreamFile` lê e grava por aqui.
  oscr::StreamSink * sink();
  oscr::StreamSource * source();

  /// Erro não fatal dos núcleos (UI::error): o comando termina com ERRO ao fim da função do núcleo.
  void noteError();

  /// O núcleo desistiu por um prompt de abortar/tentar de novo/continuar (cabeçalho inválido ou sem cartucho).
  void noteAbort();

  /// Achado do autoteste (cores/SelfTest.cpp): 1 = pino `a` em curto com GND, 2 = pinos `a` e `b` em curto, 3 = falta o pull-up de 1 kΩ no D7, 4 = sem Si5351.
  /// Pinos na numeração do Arduino (54 em diante = A0...). Só vale durante o comando SELFTEST.
  void noteSelfTest(uint8_t kind, uint8_t a, uint8_t b);

  /// Erro fatal dos núcleos (UI::fatalError*): volta ao laço de comandos sem terminar a função do núcleo.
  [[ noreturn ]] void fatal();
}
