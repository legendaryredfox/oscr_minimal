// SPDX-License-Identifier: GPL-3.0-or-later
// Roda a Session do firmware (MockBackend) ligada a stdin/stdout. Usado pelos testes do host:
// o cliente Python conversa com este processo como se fosse a porta serial.
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "../src/dumper/oscr_proto.h"
#include "../src/dumper/oscr_session.h"

static int rd(void*, uint32_t timeout_ms) {
  struct pollfd p = {0, POLLIN, 0};
  int r = poll(&p, 1, int(timeout_ms));
  if (r <= 0) return -1;
  uint8_t b;
  ssize_t n = read(0, &b, 1);
  if (n == 0) _exit(0);   // host fechou
  return n == 1 ? b : -1;
}
static void wr(void*, const uint8_t* d, size_t n) {
  size_t off = 0;
  while (off < n) { ssize_t w = write(1, d + off, n - off); if (w <= 0) _exit(1); off += size_t(w); }
}
static uint32_t now(void*) {
  struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return uint32_t(t.tv_sec * 1000UL + t.tv_nsec / 1000000UL);
}

// Backend em modo fluxo (como os núcleos do OSCR): gera os bytes aos pedaços, sem saber o tamanho antes. Uso: sim_stdio stream
struct StreamMock : oscr::MockBackend {
  static constexpr uint32_t kRom = 5000, kSave = 2000;
  bool streams() override { return true; }
  void detect(uint8_t s, oscr::DetectInfo& o) override { MockBackend::detect(s, o); o.rom_size = kRom; o.save_size = kSave; strcpy(o.name, "STREAM"); }
  bool stream_read(uint8_t, uint8_t kind, oscr::StreamSink& out, uint16_t& err) override {
    uint32_t n = kind == oscr::KIND_ROM ? kRom : kSave;
    uint8_t buf[300];
    for (uint32_t off = 0; off < n;) {                       // pedaços de 300 bytes, diferentes do bloco do protocolo
      uint32_t k = n - off < sizeof buf ? n - off : sizeof buf;
      for (uint32_t i = 0; i < k; i++) buf[i] = kind == oscr::KIND_ROM ? rom_byte(off + i) : save_byte(off + i);
      if (!out.write(buf, k)) { err = oscr::E_ABORTADO; return false; }
      off += k;
    }
    return true;
  }
  // WRITE_ROM: chip 9 "não é reconhecido" (E_FLASH, nada é lido); senão confere o mesmo padrão do save (byte i = i*5)
  uint16_t chip_ = 0, prg_ = 0, chr_ = 0;
  void set_options(uint16_t m, uint16_t p, uint16_t c) override { chip_ = m; prg_ = p; chr_ = c; }
  bool rom_prepare(uint8_t, uint32_t size, uint16_t& err) override {
    if (chip_ == 9) { err = oscr::E_FLASH; return false; }
    if (size != (uint32_t(prg_) + chr_) * 1024u) { err = oscr::E_ARGUMENTO; return false; }
    usleep(300000);                                          // "apagar": o PC tem que esperar o primeiro ACK
    return true;
  }
  bool stream_write_rom(uint8_t s, oscr::StreamSource& in, uint16_t& err) override { return stream_write(s, in, err); }
  bool stream_write(uint8_t, oscr::StreamSource& in, uint16_t& err) override {
    uint8_t buf[77];
    uint32_t off = 0;
    while (off < in.size()) {                                // lê em pedaços de 77 bytes
      size_t k = in.read(buf, sizeof buf);
      if (k == 0) { err = oscr::E_CARTUCHO_IO; return false; }
      for (size_t i = 0; i < k; i++) if (buf[i] != uint8_t((off + i) * 5)) { err = oscr::E_CARTUCHO_IO; return false; }
      off += uint32_t(k);
    }
    return true;
  }
};

int main(int argc, char** argv) {
  static uint8_t rx[OSCR_MAX_PAYLOAD], tx[OSCR_MAX_PAYLOAD + 10];
  static oscr::MockBackend plain; static StreamMock streamed;
  oscr::Backend& be = (argc > 1 && !strcmp(argv[1], "stream")) ? static_cast<oscr::Backend&>(streamed) : static_cast<oscr::Backend&>(plain);
  oscr::Session s(oscr::Io{nullptr, rd, wr, now}, be, rx, sizeof rx, tx, sizeof tx);
  for (;;) {
    struct pollfd p = {0, POLLIN, 0};
    poll(&p, 1, 50);          // espera dados sem consumir
    s.poll();
  }
}
