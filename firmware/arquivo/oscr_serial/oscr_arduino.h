// SPDX-License-Identifier: GPL-3.0-or-later
// Cola Arduino/PlatformIO: liga a Session do protocolo à Serial do Mega.
// Uso (igual nos dois projetos, ver firmware/arduino e firmware/platformio):
//   static oscr::MockBackend be;  static OscrApp app(be);
//   void setup() { app.begin(); }  void loop() { app.poll(); }
#pragma once
#ifdef ARDUINO
#include <Arduino.h>

#include "oscr_session.h"

#ifndef OSCR_BAUD
#define OSCR_BAUD 1000000UL     // 115200 como fallback: compile com -DOSCR_BAUD=115200
#endif
#ifndef OSCR_LED_PIN
#define OSCR_LED_PIN 38         // D38 (PD7): LED de status, ativo em nível baixo (docs/pinmap.md)
#endif

class OscrApp {
 public:
  explicit OscrApp(oscr::Backend& be)
      : session_(oscr::Io{this, &OscrApp::rd, &OscrApp::wr, &OscrApp::now}, be, rx_, sizeof rx_, tx_, sizeof tx_) {}

  void begin() {
    Serial.begin(OSCR_BAUD);
    pinMode(OSCR_LED_PIN, OUTPUT);
    digitalWrite(OSCR_LED_PIN, LOW);    // aceso no boot
    delay(150);
    digitalWrite(OSCR_LED_PIN, HIGH);
  }
  void poll() { session_.poll(); }

 private:
  static int rd(void*, uint32_t timeout_ms) {
    uint32_t start = millis();
    for (;;) {
      if (Serial.available()) return Serial.read();
      if (millis() - start >= timeout_ms) return -1;
    }
  }
  static void wr(void*, const uint8_t* d, size_t n) {
    digitalWrite(OSCR_LED_PIN, !digitalRead(OSCR_LED_PIN));   // pisca a cada quadro enviado
    Serial.write(d, n);
  }
  static uint32_t now(void*) { return millis(); }

  uint8_t rx_[OSCR_MAX_PAYLOAD];
  uint8_t tx_[OSCR_MAX_PAYLOAD + 10];
  oscr::Session session_;
};
#endif  // ARDUINO
