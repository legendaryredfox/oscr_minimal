// SPDX-License-Identifier: GPL-3.0-or-later
// Projeto Arduino do dumper oscr_minimal (placa: Arduino Mega 2560).
// Precisa da biblioteca "oscr_serial" (pasta firmware/oscr_serial): copie-a para a pasta de
// bibliotecas do Arduino, ou use: arduino-cli compile --library firmware/oscr_serial ...
// Modo de teste sem cartucho (dados sintéticos): compile com -DOSCR_MOCK.
#include <Wire.h>
#include <oscr_arduino.h>
#include <oscr_avr_buses.h>
#include <oscr_carts.h>

#ifdef OSCR_MOCK
static oscr::MockBackend backend;
#else
static oscr::AvrSnesBus snes;
static oscr::AvrNesBus nes;
static oscr::AvrMdBus md;
static oscr::AvrGbaBus gba;
static oscr::AvrGbBus gb;
static oscr::CartBackend backend(&snes, &nes, &md, &gba, &gb);
#endif
static OscrApp app(backend);

void setup() { app.begin(); }
void loop() { app.poll(); }
