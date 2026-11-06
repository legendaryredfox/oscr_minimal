// CIC lock do SNES no RP2040 (substitui o PIC12F629 com snescic-lock-resync.hex), decisão D89.
//
// Roda o MESMO programa do PIC (third_party/snescic-lock-resync.hex, sd2snes) num interpretador do
// PIC12F629 (pic12f629.h), uma instrução por ciclo de instrução do PIC. O relógio vem do CLK2 do
// Si5351: um programa PIO conta 4 bordas de subida do CLK2 por ciclo, então o tempo do protocolo
// acompanha o clock real (1 MHz na fase de destravar o SA-1, 3,072 MHz depois), como no PIC.
//
// Licença: GPL v2 only (o programa embutido é do sd2snes, ver third_party/ e README.md).
//
// Compilar: arduino-cli compile -b rp2040:rp2040:waveshare_rp2040_zero cic_rp2040   (CPU 200 MHz)
#include <Arduino.h>
#include <hardware/gpio.h>
#include <hardware/pio.h>

// Funções do interpretador na RAM: executar da flash (XIP) teria tempo variável.
#define CIC_RAMFUNC __attribute__((section(".time_critical.cic")))
#include "pic12f629.h"
#include "lock_prog.h"
#include "pins.h"

static uint16_t progRam[cic::Pic12F629::kProgWords];     // o programa fica na RAM
static cic::Pic12F629 pic(progRam);

static PIO  tickPio = pio1;
static uint tickSm;

constexpr uint32_t pinMask(uint8_t pin) { return 1u << pin; }
constexpr uint32_t kOutMask = pinMask(PIN_D0_OUT) | pinMask(PIN_D1_OUT) | pinMask(PIN_D0_OE) | pinMask(PIN_D1_OE) |
                              pinMask(PIN_SLAVE_OUT) | pinMask(PIN_HOST_OUT);

// Estatísticas lidas pelo core 0 (só para depuração na serial USB).
static volatile uint32_t statCycles = 0;   // ciclos de instrução do PIC já executados
static volatile uint32_t statLate = 0;     // vezes em que o RP2040 pegou o tick atrasado
static volatile uint16_t statPc = 0;
static volatile uint8_t  statGpio = 0;

// Base de tempo: um push no FIFO a cada 4 bordas de subida do CLK (um ciclo de instrução do PIC).
//   set x, 3 / wait 0 pin 0 / wait 1 pin 0 / jmp x-- (volta ao wait 0) / push noblock
static void startTickCounter() {
  // Palavras conferidas com o pioasm (tools/tick.pio): wait 0/1 pin 0 usa a origem "pin" (relativa a in_base).
  static const uint16_t code[5] = {0xE023, 0x2020, 0x20A0, 0x0041, 0x8000};
  pio_program_t prog = {};
  prog.instructions = code;
  prog.length = 5;
  prog.origin = 0;                                   // o jmp usa o endereço absoluto 1
  pio_add_program(tickPio, &prog);
  tickSm = pio_claim_unused_sm(tickPio, true);
  pio_gpio_init(tickPio, PIN_CLK);
  pio_sm_set_consecutive_pindirs(tickPio, tickSm, PIN_CLK, 1, false);
  pio_sm_config c = pio_get_default_sm_config();
  sm_config_set_wrap(&c, 0, 4);
  sm_config_set_in_pins(&c, PIN_CLK);
  sm_config_set_fifo_join(&c, PIO_FIFO_JOIN_RX);     // FIFO de 8: aguenta uma folga de ticks
  sm_config_set_clkdiv(&c, 1.0f);
  pio_sm_init(tickPio, tickSm, 0, &c);
  pio_sm_set_enabled(tickPio, tickSm, true);
}

static void setupPins() {
  const uint8_t outs[] = {PIN_D0_OUT, PIN_D1_OUT, PIN_SLAVE_OUT, PIN_HOST_OUT, PIN_D0_OE, PIN_D1_OE};
  gpio_put_masked(kOutMask, pinMask(PIN_D0_OE) | pinMask(PIN_D1_OE));   // buffers dos dados desligados
  for (uint8_t p : outs) { gpio_init(p); gpio_set_dir(p, GPIO_OUT); }
  gpio_put_masked(kOutMask, pinMask(PIN_D0_OE) | pinMask(PIN_D1_OE));
  const uint8_t ins[] = {PIN_RST_IN, PIN_D0_IN, PIN_D1_IN};
  for (uint8_t p : ins) { gpio_init(p); gpio_set_dir(p, GPIO_IN); }
}

static inline void __not_in_flash_func(waitTick)() {
  while (tickPio->fstat & (1u << (PIO_FSTAT_RXEMPTY_LSB + tickSm))) { }
  (void)tickPio->rxf[tickSm];
}

// Laço do emulador: um ciclo de instrução por tick. As saídas da instrução anterior são aplicadas
// no início do ciclo seguinte (como o PIC, que escreve o latch no fim do ciclo) e os pinos de
// entrada são amostrados logo depois.
static void __not_in_flash_func(runEmulator)() {
  uint32_t lastOut = 0xFFFFFFFFu;
  uint32_t n = 0, late = 0;
  for (;;) {
    waitTick();
    if (((tickPio->flevel >> (PIO_FLEVEL_RX0_LSB + 8 * tickSm)) & 0xF) > 1) late++;

    const uint8_t dr = pic.drive(), lv = pic.level();
    uint32_t v = 0;
    if ((lv & dr) & 0x01) v |= pinMask(PIN_D0_OUT);
    if ((lv & dr) & 0x02) v |= pinMask(PIN_D1_OUT);
    if ((lv & dr) & 0x04) v |= pinMask(PIN_SLAVE_OUT);
    if ((lv & dr) & 0x10) v |= pinMask(PIN_HOST_OUT);
    if (!(dr & 0x01)) v |= pinMask(PIN_D0_OE);               // /OE alto = buffer desligado
    if (!(dr & 0x02)) v |= pinMask(PIN_D1_OE);
    if (v != lastOut) { gpio_put_masked(kOutMask, v); lastOut = v; }

    const uint32_t g = gpio_get_all();
    pic.setPins((uint8_t)(((g >> PIN_D0_IN) & 1) | (((g >> PIN_D1_IN) & 1) << 1) | (((g >> PIN_RST_IN) & 1) << 3)));

    const uint8_t cyc = pic.step();
    for (uint8_t k = 1; k < cyc; k++) waitTick();        // instruções de 2 ciclos

    if ((++n & 0x3FF) == 0) {
      statCycles = n; statLate = late; statPc = pic.pc(); statGpio = pic.level();
    }
  }
}

// ---- core 1: o emulador (nunca retorna) ----
void setup1() {
  for (unsigned i = 0; i < cic::Pic12F629::kProgWords; i++) progRam[i] = 0x3FFF;
  for (unsigned i = 0; i < kLockProg_words; i++) progRam[i] = kLockProg[i];
  setupPins();
  startTickCounter();
  pic.reset();
}
void loop1() { runEmulator(); }

// ---- core 0: só a serial USB, para ver o estado na bancada ----
void setup() { Serial.begin(115200); }
void loop() {
  static uint32_t last = 0;
  if (millis() - last >= 1000) {
    last = millis();
    Serial.printf("ciclos=%lu atrasos=%lu pc=0x%03X latch=0x%02X\n",
                  (unsigned long)statCycles, (unsigned long)statLate, (unsigned)statPc, (unsigned)statGpio);
  }
}
