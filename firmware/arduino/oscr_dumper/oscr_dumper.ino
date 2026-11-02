// SPDX-License-Identifier: GPL-3.0-or-later
// Projeto Arduino do dumper oscr_minimal (placa: Arduino Mega 2560).
// Precisa da biblioteca "oscr_serial" (pasta firmware/oscr_serial): copie-a para a pasta
// de bibliotecas do Arduino ou use: arduino-cli compile --library firmware/oscr_serial ...
#include <oscr_arduino.h>

static oscr::MockBackend backend;   // modo MOCK: dados sintéticos, sem cartucho
static OscrApp app(backend);

void setup() { app.begin(); }
void loop() { app.poll(); }
