// SPDX-License-Identifier: GPL-3.0-or-later
// Seletor de tensão do cartucho sem hardware (D138). Código puro, sem Arduino: testado no PC em pc-tests/test_volt_core.cpp.
// (O desligamento do 5 V por software, D115 a D128, foi retirado em D139: o 5 V dos slots fica sempre ligado.)
#pragma once
#include <stdint.h>

namespace oscr { namespace volt {

/// Valores de `VoltInfo::volt`: 0 sem seletor (5 V fixo), 1 = 3,3 V, 2 = 5 V.
enum : uint8_t { kVoltNone = 0, kVolt3V3 = 1, kVolt5V = 2 };

}}  // namespace oscr::volt
