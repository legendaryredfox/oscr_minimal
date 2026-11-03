// SPDX-License-Identifier: GPL-3.0-or-later
// Mock mínimo do Arduino/avr-libc para rodar oscr_avr_buses.h no PC: cada registrador grava as escritas num trace.
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <utility>
#include <vector>

inline std::vector<std::pair<const char*, uint8_t>>& hal_trace() { static std::vector<std::pair<const char*, uint8_t>> t; return t; }
inline unsigned long& hal_delay_ms() { static unsigned long d = 0; return d; }

struct HalReg {
  const char* n; uint8_t v;
  explicit HalReg(const char* name) : n(name), v(0) {}
  operator uint8_t() const { return v; }                                   // leitura (PINx devolve o que o teste puser em v)
  HalReg& operator=(uint8_t x) { set(x); return *this; }
  HalReg& operator|=(uint8_t x) { set(uint8_t(v | x)); return *this; }
  HalReg& operator&=(uint8_t x) { set(uint8_t(v & x)); return *this; }
  HalReg& operator^=(uint8_t x) { set(uint8_t(v ^ x)); return *this; }
  void set(uint8_t x) { v = x; hal_trace().push_back(std::make_pair(n, x)); }
};

#define HAL_REGS(X) static HalReg PORT##X("PORT" #X), DDR##X("DDR" #X), PIN##X("PIN" #X);
HAL_REGS(A) HAL_REGS(C) HAL_REGS(D) HAL_REGS(E) HAL_REGS(F) HAL_REGS(G) HAL_REGS(H) HAL_REGS(J) HAL_REGS(K) HAL_REGS(L)

inline void delay(unsigned long ms) { hal_delay_ms() += ms; }
inline void delayMicroseconds(unsigned int) {}
inline void noInterrupts() {}
inline void interrupts() {}
