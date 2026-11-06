// Ligações do RP2040-Zero ao circuito do CIC (números = GPIO do RP2040).
//
// O módulo RP2040-Zero tem na borda esquerda, de cima para baixo: 5V, GND, 3V3, GP29, GP28, GP27,
// GP26, GP15, GP14; na borda direita GP0..GP8; embaixo GP13..GP9 (Waveshare, 2,54 mm).
// Esta atribuição é PROVISÓRIA: fecha-se quando o esquemático da v1.3 for desenhado.
//
// Nomes pelo PIC12F629 que o RP2040 substitui (pino do PIC entre parênteses):
//   GP0 (7) dados 0, slot 55   bidirecional    GP3 (4) reset de entrada, D40/PG1 do Mega
//   GP1 (6) dados 1, slot 24   bidirecional    GP4 (3) reset do host, D41/PG0 do Mega
//   GP2 (5) reset do escravo, slot 25 (saída)  GP5 (2) clock CLK2 do Si5351 (entrada)
//
// Níveis: o RP2040 é 3,3 V e não aceita 5 V nos pinos.
//   *_IN  recebem 5 V por divisor resistivo (por exemplo 2,0 kΩ em série e 3,3 kΩ para o GND).
//   *_OUT vão a um 74HCT125 alimentado com 5 V (entrada TTL aceita 3,3 V; saída em 5 V).
//   *_OE  é o /OE do 74HCT125: nível BAIXO habilita a saída. Os dados 0 e 1 trocam de sentido
//         durante a autenticação, então cada um usa uma porta com OE próprio mais o divisor de entrada.
//         O /OE precisa de pull-up ao 3V3 (10 kΩ) para o buffer ficar desligado antes do firmware subir.
//   O CLK2 do Si5351 entra direto (ver o nível do módulo com o osciloscópio antes de ligar).
#pragma once
#include <stdint.h>

constexpr uint8_t PIN_CLK       = 29;  // entrada, borda de subida marca o tempo do PIC
constexpr uint8_t PIN_RST_IN    = 28;  // GP3 do PIC: D40 (PG1) do Mega, via divisor
constexpr uint8_t PIN_D0_IN     = 26;  // GP0 do PIC lido: slot 55, via divisor
constexpr uint8_t PIN_D1_IN     = 27;  // GP1 do PIC lido: slot 24, via divisor
constexpr uint8_t PIN_D0_OUT    = 15;  // GP0 do PIC escrito: entrada do 74HCT125 (porta A)
constexpr uint8_t PIN_D1_OUT    = 14;  // GP1 do PIC escrito: entrada do 74HCT125 (porta B)
constexpr uint8_t PIN_D0_OE     = 0;   // /OE da porta A (baixo = o RP2040 dirige o slot 55)
constexpr uint8_t PIN_D1_OE     = 1;   // /OE da porta B (baixo = o RP2040 dirige o slot 24)
constexpr uint8_t PIN_SLAVE_OUT = 2;   // GP2 do PIC: reset do escravo, slot 25 (porta C, /OE no GND)
constexpr uint8_t PIN_HOST_OUT  = 3;   // GP4 do PIC: reset do host, D41 (porta D, /OE no GND)
