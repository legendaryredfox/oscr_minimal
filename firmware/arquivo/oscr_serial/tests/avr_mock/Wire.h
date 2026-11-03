// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <stdint.h>
#include <vector>
#include "Arduino.h"

struct MockWire {
  std::vector<std::vector<uint8_t> > tx; std::vector<uint8_t> cur; bool ack = true; int begins = 0;
  void begin() { begins++; PORTD |= 0x03; }   // o twi_init real liga os pull-ups de SDA (PD1) e SCL (PD0)
  void beginTransmission(uint8_t) { cur.clear(); }
  size_t write(uint8_t b) { cur.push_back(b); return 1; }
  uint8_t endTransmission() { tx.push_back(cur); return ack ? 0 : 2; }
};
static MockWire Wire;
