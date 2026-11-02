// SPDX-License-Identifier: GPL-3.0-or-later
// Projeto PlatformIO do dumper oscr_minimal. Mesmo código do projeto Arduino.
#include <Arduino.h>
#include <oscr_arduino.h>

static oscr::MockBackend backend;   // modo MOCK: dados sintéticos, sem cartucho
static OscrApp app(backend);

void setup() { app.begin(); }
void loop() { app.poll(); }
