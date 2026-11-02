// SPDX-License-Identifier: GPL-3.0-or-later
// Projeto PlatformIO do dumper oscr_minimal. Mesmo código do projeto Arduino.
// Ambiente "megaatmega2560_mock": dados sintéticos, sem cartucho (-DOSCR_MOCK).
#include <Arduino.h>
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
static oscr::CartBackend backend(&snes, &nes, &md, &gba);
#endif
static OscrApp app(backend);

void setup() { app.begin(); }
void loop() { app.poll(); }
