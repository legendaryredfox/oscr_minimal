// Roda a Session do firmware (MockBackend) ligada a stdin/stdout. Usado pelos testes do host:
// o cliente Python conversa com este processo como se fosse a porta serial.
#include <poll.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>

#include "../oscr_proto.h"
#include "../oscr_session.h"

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

int main() {
  static uint8_t rx[OSCR_MAX_PAYLOAD], tx[OSCR_MAX_PAYLOAD + 10];
  oscr::MockBackend be;
  oscr::Session s(oscr::Io{nullptr, rd, wr, now}, be, rx, sizeof rx, tx, sizeof tx);
  for (;;) {
    struct pollfd p = {0, POLLIN, 0};
    poll(&p, 1, 50);          // espera dados sem consumir
    s.poll();
  }
}
