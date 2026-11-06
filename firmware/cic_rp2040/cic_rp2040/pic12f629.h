// Interpretador de instruções do PIC12F629 (núcleo de 14 bits, 35 instruções).
//
// Serve para rodar o snescic-lock-resync.hex do sd2snes (third_party/) dentro do RP2040,
// no lugar do PIC (decisão D89). O código é puro C++ (sem Arduino), usado também pelo
// simulador de PC em test/.
//
// Escopo: o que os programas snescic-lock-resync e snescic-key usam: GPIO, TRISIO, OPTION_REG,
// INTCON (interrupção externa em GP2), EEPROM de dados, FSR/INDF e pilha de 8 níveis.
// Temporizadores, comparador, ADC e watchdog não são simulados (nenhum dos dois programas usa).
// Memória de dados: os GPR 0x20..0x5F aparecem também em 0xA0..0xDF (espelho; o chip real
// não usa isso nos dois programas).
//
// Modelo de tempo: step() executa UMA instrução e devolve quantos ciclos de instrução ela
// gastou (1 ou 2; 3 na entrada de interrupção). Um ciclo = 4 ciclos do clock externo (CLKIN).
// O chamador aplica os níveis dos pinos (setPins) antes de step() e lê drive()/level() depois.
//
// Licença: GPL v2 only, como o programa que ele roda (ver third_party/ e README.md).
#pragma once
#include <stdint.h>

#ifndef CIC_RAMFUNC
#define CIC_RAMFUNC
#endif

namespace cic {

class Pic12F629 {
 public:
  static constexpr uint16_t kProgWords = 1024;

  // prog: kProgWords palavras de 14 bits (endereço de palavra). Precisa ficar válido.
  explicit Pic12F629(const uint16_t* prog) : prog_(prog) { reset(); }

  void reset() {
    pc_ = 0; w_ = 0; sp_ = 0;
    status_ = 0x18; fsr_ = 0; pclath_ = 0; intcon_ = 0;
    option_ = 0xFF; tris_ = 0x3F; latch_ = 0; wpu_ = 0x37; ioc_ = 0x00;
    cmcon_ = 0; pir1_ = 0; pie1_ = 0; pcon_ = 0; osccal_ = 0; vrcon_ = 0;
    eedata_ = 0; eeadr_ = 0; eecon1_ = 0; eeseq_ = 0;
    pins_ = 0; prevInt_ = 0; sleeping_ = false;
    for (int i = 0; i < 64; i++) ram_[i] = 0;
  }

  // Níveis que o mundo externo coloca nos pinos GP0..GP5 (bit n = GPn). Só vale para pinos
  // que o PIC deixa como entrada; os de saída seguem o latch.
  void setPins(uint8_t ext) { pins_ = ext & 0x3F; }

  // Pinos que o PIC está dirigindo (bit n = 1: GPn é saída) e o nível que ele coloca.
  uint8_t drive() const { return (uint8_t)(~tris_ & 0x37); }   // GP3 só entrada
  uint8_t level() const { return latch_ & 0x37; }
  // Nível visto em cada pino agora (entrada externa ou latch, conforme a direção).
  uint8_t pinLevels() const {
    uint8_t d = drive();
    return (uint8_t)((latch_ & d) | (pins_ & ~d & 0x3F));
  }
  // Pull-ups fracos ligados (WPUA e OPTION_REG<7>): o ambiente pode usar para pinos soltos.
  uint8_t weakPullups() const { return (option_ & 0x80) ? 0 : (uint8_t)(wpu_ & tris_ & 0x37); }

  uint16_t pc() const { return pc_; }
  uint8_t  gpr(uint8_t addr) const { return (addr >= 0x20 && addr < 0x60) ? ram_[addr - 0x20] : 0; }  // só para testes
  uint8_t  w() const { return w_; }
  bool     sleeping() const { return sleeping_; }
  uint8_t  eeprom[128] = {0};   // EEPROM de dados (pré-carregue antes de rodar, se o programa ler)

  CIC_RAMFUNC uint8_t step() {
    // --- interrupção externa em GP2 (INTE): borda conforme OPTION_REG<6> ---
    uint8_t pin2 = (pinLevels() >> 2) & 1;
    bool edge = (option_ & 0x40) ? (pin2 && !prevInt_) : (!pin2 && prevInt_);
    prevInt_ = pin2;
    if (edge) intcon_ |= 0x02;                                  // INTF
    if ((intcon_ & 0x80) && (intcon_ & 0x10) && (intcon_ & 0x02)) {  // GIE e INTE e INTF
      sleeping_ = false;
      push(pc_);
      intcon_ &= (uint8_t)~0x80;
      pc_ = 4;
      return 3;
    }
    if (sleeping_) return 1;

    const uint16_t op = fetch(pc_);
    pc_ = (uint16_t)((pc_ + 1) & (kProgWords - 1));
    uint8_t cyc = 1;
    const uint8_t f = op & 0x7F;
    const bool d = (op & 0x80) != 0;

    switch ((op >> 12) & 3) {
      case 0: {  // orientadas a byte
        switch ((op >> 8) & 0xF) {
          case 0x0:
            if (op & 0x80) { wr(f, w_); break; }                // MOVWF
            switch (op) {
              case 0x0008: pc_ = pop(); cyc = 2; break;         // RETURN
              case 0x0009: pc_ = pop(); intcon_ |= 0x80; cyc = 2; break;  // RETFIE
              case 0x0063: sleeping_ = true; break;             // SLEEP (acorda só por interrupção)
              default: break;                                   // NOP, CLRWDT
            }
            break;
          case 0x1:
            if (op & 0x80) { wr(f, 0); setZ(true); }            // CLRF
            else { w_ = 0; setZ(true); }                        // CLRW
            break;
          case 0x2: { uint8_t r = sub(rd(f), w_); store(f, d, r); break; }          // SUBWF
          case 0x3: { uint8_t r = (uint8_t)(rd(f) - 1); setZ(r == 0); store(f, d, r); break; }  // DECF
          case 0x4: { uint8_t r = rd(f) | w_; setZ(r == 0); store(f, d, r); break; }            // IORWF
          case 0x5: { uint8_t r = rd(f) & w_; setZ(r == 0); store(f, d, r); break; }            // ANDWF
          case 0x6: { uint8_t r = rd(f) ^ w_; setZ(r == 0); store(f, d, r); break; }            // XORWF
          case 0x7: { uint8_t r = add(rd(f), w_); store(f, d, r); break; }                      // ADDWF
          case 0x8: { uint8_t r = rd(f); setZ(r == 0); store(f, d, r); break; }                 // MOVF
          case 0x9: { uint8_t r = (uint8_t)~rd(f); setZ(r == 0); store(f, d, r); break; }       // COMF
          case 0xA: { uint8_t r = (uint8_t)(rd(f) + 1); setZ(r == 0); store(f, d, r); break; }  // INCF
          case 0xB: { uint8_t r = (uint8_t)(rd(f) - 1); store(f, d, r);
                      if (r == 0) { pc_ = (uint16_t)((pc_ + 1) & (kProgWords - 1)); cyc = 2; } break; }  // DECFSZ
          case 0xC: { uint8_t v = rd(f), c = status_ & 1;
                      uint8_t r = (uint8_t)((v >> 1) | (c << 7));
                      setC(v & 1); store(f, d, r); break; }                                     // RRF
          case 0xD: { uint8_t v = rd(f), c = status_ & 1;
                      uint8_t r = (uint8_t)((v << 1) | c);
                      setC(v >> 7); store(f, d, r); break; }                                    // RLF
          case 0xE: { uint8_t v = rd(f); store(f, d, (uint8_t)((v << 4) | (v >> 4))); break; }  // SWAPF
          case 0xF: { uint8_t r = (uint8_t)(rd(f) + 1); store(f, d, r);
                      if (r == 0) { pc_ = (uint16_t)((pc_ + 1) & (kProgWords - 1)); cyc = 2; } break; }  // INCFSZ
        }
        break;
      }
      case 1: {  // orientadas a bit
        const uint8_t b = (op >> 7) & 7;
        switch ((op >> 10) & 3) {
          case 0: wr(f, (uint8_t)(rd(f) & ~(1u << b))); break;      // BCF
          case 1: wr(f, (uint8_t)(rd(f) | (1u << b))); break;       // BSF
          case 2: if (!((rd(f) >> b) & 1)) { pc_ = (uint16_t)((pc_ + 1) & (kProgWords - 1)); cyc = 2; } break;  // BTFSC
          case 3: if ((rd(f) >> b) & 1) { pc_ = (uint16_t)((pc_ + 1) & (kProgWords - 1)); cyc = 2; } break;     // BTFSS
        }
        break;
      }
      case 2: {  // CALL / GOTO
        uint16_t k = (uint16_t)((((pclath_ & 0x18) << 8) | (op & 0x7FF)) & (kProgWords - 1));
        if (!(op & 0x800)) push(pc_);                               // CALL guarda o retorno
        pc_ = k; cyc = 2;
        break;
      }
      case 3: {  // literais
        const uint8_t k = op & 0xFF;
        switch ((op >> 8) & 0xF) {
          case 0x0: case 0x1: case 0x2: case 0x3: w_ = k; break;                            // MOVLW
          case 0x4: case 0x5: case 0x6: case 0x7: w_ = k; pc_ = pop(); cyc = 2; break;      // RETLW
          case 0x8: w_ |= k; setZ(w_ == 0); break;                                          // IORLW
          case 0x9: w_ &= k; setZ(w_ == 0); break;                                          // ANDLW
          case 0xA: w_ ^= k; setZ(w_ == 0); break;                                          // XORLW
          case 0xC: case 0xD: w_ = sub(k, w_); break;                                       // SUBLW
          case 0xE: case 0xF: w_ = add(k, w_); break;                                       // ADDLW
          default: break;
        }
        break;
      }
    }
    return cyc;
  }

 private:
  uint16_t fetch(uint16_t a) const { return (uint16_t)(prog_[a] & 0x3FFF); }
  void push(uint16_t v) { stack_[sp_ & 7] = v; sp_++; }
  uint16_t pop() { sp_--; return stack_[sp_ & 7]; }

  CIC_RAMFUNC void setZ(bool z) { status_ = (uint8_t)((status_ & ~0x04) | (z ? 0x04 : 0)); }
  CIC_RAMFUNC void setC(unsigned c) { status_ = (uint8_t)((status_ & ~0x01) | (c & 1)); }
  CIC_RAMFUNC void setDC(bool c) { status_ = (uint8_t)((status_ & ~0x02) | (c ? 0x02 : 0)); }
  CIC_RAMFUNC uint8_t add(uint8_t a, uint8_t b) {
    unsigned r = (unsigned)a + b;
    setC(r > 0xFF); setDC(((a & 0xF) + (b & 0xF)) > 0xF);
    setZ((r & 0xFF) == 0);
    return (uint8_t)r;
  }
  CIC_RAMFUNC uint8_t sub(uint8_t a, uint8_t b) {   // a - b; C = 1 se não houve empréstimo
    uint8_t r = (uint8_t)(a - b);
    setC(a >= b); setDC((a & 0xF) >= (b & 0xF)); setZ(r == 0);
    return r;
  }
  void store(uint8_t f, bool toF, uint8_t v) { if (toF) wr(f, v); else w_ = v; }

  // Leitura/escrita do arquivo de registradores; f = endereço de 7 bits, banco = STATUS<5>.
  CIC_RAMFUNC uint8_t rd(uint8_t f) const { return rdAbs((uint8_t)(f | ((status_ & 0x20) << 2))); }
  CIC_RAMFUNC void wr(uint8_t f, uint8_t v) { wrAbs((uint8_t)(f | ((status_ & 0x20) << 2)), v); }

  CIC_RAMFUNC uint8_t rdAbs(uint8_t x) const {
    switch (x & 0x7F) {
      case 0x00: { uint8_t i = fsr_; return ((i & 0x7F) == 0) ? 0 : rdAbs(i); }  // INDF
      case 0x02: return (uint8_t)(pc_ & 0xFF);
      case 0x03: return status_;
      case 0x04: return fsr_;
      case 0x0A: return pclath_;
      case 0x0B: return intcon_;
      default: break;
    }
    if (x < 0x80) {
      switch (x) {
        case 0x01: return 0;                    // TMR0 (não simulado)
        case 0x05: return pinLevels();
        case 0x0C: return pir1_;
        case 0x19: return cmcon_;
        default: break;
      }
    } else {
      switch (x) {
        case 0x81: return option_;
        case 0x85: return (uint8_t)(tris_ | 0x08);
        case 0x8C: return pie1_;
        case 0x8E: return pcon_;
        case 0x90: return osccal_;
        case 0x95: return wpu_;
        case 0x96: return ioc_;
        case 0x99: return vrcon_;
        case 0x9A: return eedata_;
        case 0x9B: return eeadr_;
        case 0x9C: return eecon1_;
        case 0x9D: return 0;                    // EECON2 lê 0
        default: break;
      }
    }
    uint8_t g = x & 0x7F;
    if (g >= 0x20 && g < 0x60) return ram_[g - 0x20];
    return 0;
  }

  CIC_RAMFUNC void wrAbs(uint8_t x, uint8_t v) {
    switch (x & 0x7F) {
      case 0x00: { uint8_t i = fsr_; if ((i & 0x7F) != 0) wrAbs(i, v); return; }   // INDF
      case 0x02: pc_ = (uint16_t)((((pclath_ & 0x1F) << 8) | v) & (kProgWords - 1)); return;   // PCL
      case 0x03: status_ = (uint8_t)((status_ & 0x18) | (v & 0xE7)); return;
      case 0x04: fsr_ = v; return;
      case 0x0A: pclath_ = v & 0x1F; return;
      case 0x0B: intcon_ = v; return;
      default: break;
    }
    if (x < 0x80) {
      switch (x) {
        case 0x05: latch_ = v & 0x3F; return;
        case 0x0C: pir1_ = v; return;
        case 0x19: cmcon_ = v; return;
        default: break;
      }
    } else {
      switch (x) {
        case 0x81: option_ = v; return;
        case 0x85: tris_ = (uint8_t)((v & 0x3F) | 0x08); return;
        case 0x8C: pie1_ = v; return;
        case 0x8E: pcon_ = v; return;
        case 0x90: osccal_ = v; return;
        case 0x95: wpu_ = v; return;
        case 0x96: ioc_ = v; return;
        case 0x99: vrcon_ = v; return;
        case 0x9A: eedata_ = v; return;
        case 0x9B: eeadr_ = v; return;
        case 0x9C: eeControl(v); return;
        case 0x9D:
          if (v == 0x55) eeseq_ = 1; else if (v == 0xAA && eeseq_ == 1) eeseq_ = 2; else eeseq_ = 0;
          return;
        default: break;
      }
    }
    uint8_t g = x & 0x7F;
    if (g >= 0x20 && g < 0x60) ram_[g - 0x20] = v;
  }

  void eeControl(uint8_t v) {
    eecon1_ = (uint8_t)(v & 0x0F);
    if ((v & 0x01) && !(v & 0x02)) {                 // RD
      eedata_ = eeprom[eeadr_ & 0x7F];
      eecon1_ &= (uint8_t)~0x01;
    }
    if ((v & 0x02) && (v & 0x04) && eeseq_ == 2) {   // WR com WREN e a sequência 55h/AAh
      eeprom[eeadr_ & 0x7F] = eedata_;
      pir1_ |= 0x80;                                 // EEIF
      eecon1_ &= (uint8_t)~0x02;
    } else if (v & 0x02) {
      eecon1_ &= (uint8_t)~0x02;                     // WR sem sequência: ignorado
    }
    eeseq_ = 0;
  }

  const uint16_t* prog_;
  uint16_t pc_, stack_[8] = {0};
  uint8_t  sp_, w_, status_, fsr_, pclath_, intcon_, option_, tris_, latch_, wpu_, ioc_;
  uint8_t  cmcon_, pir1_, pie1_, pcon_, osccal_, vrcon_, eedata_, eeadr_, eecon1_, eeseq_;
  uint8_t  pins_, prevInt_;
  bool     sleeping_;
  uint8_t  ram_[64];
};

}  // namespace cic
