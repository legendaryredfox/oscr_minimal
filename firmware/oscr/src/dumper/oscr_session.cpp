// SPDX-License-Identifier: GPL-3.0-or-later
#include "oscr_session.h"

#include <string.h>

namespace oscr {

// ---------------------------------------------------------------- MockBackend
void MockBackend::detect(uint8_t s, DetectInfo& o) {
  if (!supports(s)) { o.status = 2; return; }
  o.status = 0; o.rom_size = kRomSize; o.save_size = kSaveSize; o.save_type = 1;
  strcpy(o.name, "MOCK");
}
bool MockBackend::open_read(uint8_t s, uint8_t kind, uint32_t& size, uint16_t& err) {
  if (!supports(s)) { err = E_SISTEMA; return false; }
  size = (kind == KIND_ROM) ? kRomSize : kSaveSize;
  return true;
}
bool MockBackend::read(uint8_t, uint8_t kind, uint32_t off, uint8_t* buf, uint16_t len) {
  for (uint16_t i = 0; i < len; i++) buf[i] = (kind == KIND_ROM) ? rom_byte(off + i) : save_byte(off + i);
  return true;
}
bool MockBackend::write_begin(uint8_t s, uint32_t size, uint16_t& err) {
  if (!supports(s)) { err = E_SISTEMA; return false; }
  if (size == 0 || size > (1UL << 20)) { err = E_ARGUMENTO; return false; }
  return true;
}

// ---------------------------------------------------------------- Session
void Session::send(uint8_t type, uint8_t seq, const uint8_t* payload, uint16_t len) {
  size_t n = encode_frame(tx_, type, seq, payload, len);
  io_.write(io_.ctx, tx_, n);
}

void Session::send_error(uint8_t seq, uint16_t code, const char* text) {
  uint8_t p[3 + 32];
  uint8_t n = 0;
  while (text[n] && n < 32) { p[3 + n] = uint8_t(text[n]); n++; }
  put_u16(p, code); p[2] = n;
  send(T_ERRO, seq, p, 3 + n);
}

void Session::send_offset(uint8_t type, uint8_t seq, uint32_t off) {
  uint8_t p[4];
  put_u32(p, off);
  send(type, seq, p, 4);
}

bool Session::next_frame(uint32_t timeout_ms) {
  uint32_t start = io_.now_ms(io_.ctx);
  for (;;) {
    uint32_t now = io_.now_ms(io_.ctx);
    uint32_t left = (now - start >= timeout_ms) ? 0 : timeout_ms - (now - start);
    int b = io_.read_byte(io_.ctx, left > 20 ? 20 : left);
    if (b < 0) {
      if (!dec_.idle() && io_.now_ms(io_.ctx) - last_byte_ms_ > 200) dec_.reset();  // quadro parado no meio
      if (io_.now_ms(io_.ctx) - start >= timeout_ms) return false;
      continue;
    }
    last_byte_ms_ = io_.now_ms(io_.ctx);
    if (dec_.push(uint8_t(b))) return true;
  }
}

void Session::poll() {
  // consome sem bloquear até achar um quadro
  for (;;) {
    int b = io_.read_byte(io_.ctx, 0);
    if (b < 0) {
      if (!dec_.idle() && io_.now_ms(io_.ctx) - last_byte_ms_ > 200) dec_.reset();
      return;
    }
    last_byte_ms_ = io_.now_ms(io_.ctx);
    if (dec_.push(uint8_t(b))) { handle(); return; }
  }
}

void Session::handle() {
  uint8_t seq = dec_.seq;
  const uint8_t* p = dec_.payload();
  uint16_t len = dec_.len;
  switch (dec_.type) {
    case T_INFO: do_info(seq); break;
    case T_DETECT:
      // campos opcionais no fim (programador de flash genérico): u16 chip, u16 prg_kb, u16 chr_kb
      be_.set_options(len >= 3 ? get_u16(p + 1) : 0, len >= 5 ? get_u16(p + 3) : 0, len >= 7 ? get_u16(p + 5) : 0);
      do_detect(seq, len >= 1 ? p[0] : 0);
      break;
    case T_ERASE: do_erase(seq, p, len); break;
    case T_VOLT: do_volt(seq, p, len); break;
    case T_SELFTEST: do_selftest(seq); break;
    case T_DUMP_ROM:
    case T_READ_SAVE:
      do_read(seq, dec_.type, len >= 1 ? p[0] : 0, len >= 3 ? get_u16(p + 1) : 0, p + 3, len >= 3 ? len - 3 : 0);
      break;
    case T_WRITE_SAVE: do_write(seq, p, len); break;
    case T_WRITE_ROM: do_write(seq, p, len, KIND_ROM); break;
    case T_ABORT: send_offset(T_D_ACK, seq, 0); break;
    default: send_error(seq, E_COMANDO, "cmd"); break;
  }
  be_.set_options(0, 0, 0);   // as opções valem para um comando só; nenhum estado herdado (inclusive nos erros precoces)
}

void Session::do_info(uint8_t seq) {
  uint8_t p[9] = {PROTO_VERSION, 0, 1, 0, uint8_t(be_.flags() | (be_.volt_select() ? 32 : 0) | (be_.selftest_supported() ? 64 : 0)), 0, 0, 0, 0};   // bit5: seletor de tensão (D138); bit6: SELFTEST
  put_u16(p + 5, be_.systems());
  put_u16(p + 7, OSCR_MAX_PAYLOAD);   // campo acrescentado ao fim (docs/referencia/protocolo.md, seção 3)
  send(T_INFO_RESP, seq, p, 9);
}

void Session::do_detect(uint8_t seq, uint8_t sys) {
  DetectInfo d;
  be_.detect(sys, d);
  uint8_t p[12 + 32 + 1];
  uint8_t n = uint8_t(strlen(d.name));
  p[0] = sys; p[1] = d.status;
  put_u32(p + 2, d.rom_size); put_u32(p + 6, d.save_size);
  p[10] = d.save_type; p[11] = n;
  memcpy(p + 12, d.name, n);
  uint16_t total = 12 + n;
  send(T_DETECT_RESP, seq, p, total);
}

void Session::do_erase(uint8_t seq, const uint8_t* p, uint16_t len) {
  if (len < 7) { send_error(seq, E_ARGUMENTO, "args"); return; }
  uint8_t sys = p[0];
  if (!be_.supports(sys)) { send_error(seq, E_SISTEMA); return; }
  be_.set_options(get_u16(p + 1), get_u16(p + 3), get_u16(p + 5));
  uint16_t err = E_CARTUCHO_IO;
  if (!be_.erase(sys, err)) { send_error(seq, err); return; }
  send_offset(T_D_ACK, seq, 0);
}

void Session::do_volt(uint8_t seq, const uint8_t* p, uint16_t len) {
  if (len < 1 || p[0] > VOLT_5V) { send_error(seq, E_ARGUMENTO, "args"); return; }
  if (p[0] != VOLT_STATUS) {                    // escolhe a tensão: precisa do seletor
    uint16_t err = E_COMANDO;
    if (!be_.volt_select() || !be_.cart_voltage(p[0], err)) { send_error(seq, err, "sem seletor"); return; }
  }
  VoltInfo vi;
  be_.volt_info(vi);
  uint8_t r[3] = {uint8_t(vi.select ? 1 : 0), vi.volt, uint8_t(vi.chosen ? 1 : 0)};
  send(T_VOLT_RESP, seq, r, 3);
}

void Session::do_selftest(uint8_t seq) {
  if (!be_.selftest_supported()) { send_error(seq, E_COMANDO, "sem autoteste"); return; }
  SelfTestReport r;
  uint16_t err = E_CARTUCHO_IO;
  if (!be_.selftest(r, err)) { send_error(seq, err); return; }
  uint8_t p[2 + SelfTestReport::kMax * 3];
  p[0] = r.truncated ? 1 : 0;
  p[1] = r.n;
  memcpy(p + 2, r.item, size_t(r.n) * 3);
  send(T_SELFTEST_RESP, seq, p, uint16_t(2 + r.n * 3));
}

int Session::wait_ack(uint8_t seq, uint32_t off, uint32_t timeout_ms) {
  uint32_t start = io_.now_ms(io_.ctx);
  for (;;) {
    uint32_t el = io_.now_ms(io_.ctx) - start;
    if (el >= timeout_ms) return 0;
    if (!next_frame(timeout_ms - el)) return 0;
    if (dec_.type == T_ABORT) return -1;
    if (dec_.seq != seq || dec_.len < 4) continue;
    if (get_u32(dec_.payload()) != off) continue;
    if (dec_.type == T_ACK) return 1;
    if (dec_.type == T_NAK) return 0;
  }
}

void Session::do_read(uint8_t seq, uint8_t type, uint8_t sys, uint16_t block, const uint8_t* opt, uint16_t opt_len) {
  if (!be_.supports(sys)) { send_error(seq, E_SISTEMA); return; }
  // campos opcionais no fim do payload: u16 mapper, u16 prg_kb, u16 chr_kb (copiados antes de reusar o buffer)
  uint16_t mapper = opt_len >= 2 ? get_u16(opt) : 0, prg_kb = opt_len >= 4 ? get_u16(opt + 2) : 0, chr_kb = opt_len >= 6 ? get_u16(opt + 4) : 0;
  be_.set_options(mapper, prg_kb, chr_kb);
  if (block == 0) block = DEFAULT_BLOCK;
  if (block > OSCR_MAX_PAYLOAD - 4 || !in_tx_ok(uint16_t(block + 4))) { send_error(seq, E_ARGUMENTO, "bloco"); return; }
  uint8_t kind = (type == T_DUMP_ROM) ? KIND_ROM : KIND_SAVE;
  if (be_.streams()) { do_stream_read(seq, kind, sys, block); return; }
  uint32_t size = 0;
  uint16_t err = E_CARTUCHO_IO;
  if (!be_.open_read(sys, kind, size, err)) { send_error(seq, err); return; }

  uint8_t bp[7] = {kind, 0, 0, 0, 0, 0, 0};
  put_u32(bp + 1, size); put_u16(bp + 5, block);
  int r = 0;
  for (int t = 0; t < 4 && r == 0; t++) {
    send(T_BEGIN, seq, bp, 7);
    r = wait_ack(seq, 0, 500);
  }
  if (r <= 0) { be_.close_read(); send_error(seq, r < 0 ? E_ABORTADO : E_REENVIOS, "begin"); return; }

  uint32_t crc = 0;
  for (uint32_t off = 0; off < size; off += block) {
    uint16_t n = (size - off < block) ? uint16_t(size - off) : block;
    put_u32(tx_ + 6, off);
    if (!be_.read(sys, kind, off, tx_ + 10, n)) { be_.close_read(); send_error(seq, E_CARTUCHO_IO); return; }
    crc = crc32_update(crc, tx_ + 10, n);
    // monta o quadro DATA já com os dados lidos (cabeçalho + offset + dados + CRC32)
    tx_[0] = MAGIC0; tx_[1] = MAGIC1; tx_[2] = T_DATA; tx_[3] = seq;
    put_u16(tx_ + 4, uint16_t(4 + n));
    put_u32(tx_ + 6 + 4 + n, crc32_update(0, tx_ + 2, 4 + 4 + n));
    size_t frame = size_t(10) + 4 + n;
    r = 0;
    for (int t = 0; t < 4 && r == 0; t++) {
      io_.write(io_.ctx, tx_, frame);   // o mesmo buffer é reenviado em caso de NAK/timeout
      r = wait_ack(seq, off, 400);
    }
    if (r <= 0) { be_.close_read(); send_error(seq, r < 0 ? E_ABORTADO : E_REENVIOS, "bloco"); return; }
  }
  be_.close_read();
  uint8_t ep[8];
  put_u32(ep, size); put_u32(ep + 4, crc);
  r = 0;
  for (int t = 0; t < 4 && r == 0; t++) {
    send(T_END, seq, ep, 8);
    r = wait_ack(seq, size, 500);
  }
  if (r <= 0) send_error(seq, r < 0 ? E_ABORTADO : E_REENVIOS, "end");
}

void Session::do_write(uint8_t seq, const uint8_t* p, uint16_t len, uint8_t kind) {
  if (len < 7) { send_error(seq, E_ARGUMENTO); return; }
  uint8_t sys = p[0];
  uint32_t size = get_u32(p + 1);
  if (!be_.supports(sys)) { send_error(seq, E_SISTEMA); return; }
  be_.set_options(len >= 9 ? get_u16(p + 7) : 0, len >= 11 ? get_u16(p + 9) : 0, len >= 13 ? get_u16(p + 11) : 0);   // NES/Famicom: mapper (opcional)
  if (kind == KIND_ROM && !be_.streams()) { send_error(seq, E_COMANDO, "rom"); return; }   // WRITE_ROM só existe no modo fluxo
  if (be_.streams()) { do_stream_write(seq, sys, size, kind); return; }
  uint16_t err = E_CARTUCHO_IO;
  if (!be_.write_begin(sys, size, err)) { send_error(seq, err); return; }
  send_offset(T_D_ACK, seq, 0);
  uint32_t expected = 0, crc = 0;
  uint32_t last = io_.now_ms(io_.ctx);
  while (io_.now_ms(io_.ctx) - last < 5000) {
    if (!next_frame(200)) continue;
    if (dec_.type == T_ABORT) { be_.write_abort(); send_offset(T_D_ACK, seq, 0); return; }
    if (dec_.seq != seq) continue;
    last = io_.now_ms(io_.ctx);
    if (dec_.type == T_H_DATA && dec_.len >= 4) {
      uint32_t off = get_u32(dec_.payload());
      uint16_t n = dec_.len - 4;
      if (off == expected && uint32_t(off) + n <= size) {
        if (!be_.write_block(off, dec_.payload() + 4, n)) { be_.write_abort(); send_error(seq, E_CARTUCHO_IO); return; }
        crc = crc32_update(crc, dec_.payload() + 4, n);
        expected += n;
        send_offset(T_D_ACK, seq, off);
      } else if (off < expected) {
        send_offset(T_D_ACK, seq, off);
      }
    } else if (dec_.type == T_H_END && dec_.len >= 8) {
      uint32_t total = get_u32(dec_.payload()), hcrc = get_u32(dec_.payload() + 4);
      if (total != size || expected != size || hcrc != crc) { be_.write_abort(); send_error(seq, E_CRC); return; }
      if (!be_.write_commit()) { send_error(seq, E_CARTUCHO_IO); return; }
      send_offset(T_D_ACK, seq, total);
      return;
    }
  }
  be_.write_abort();
  send_error(seq, E_REENVIOS, "timeout");
}

// ---------------------------------------------------------------- modo fluxo (núcleos do OSCR)
// Dispositivo -> PC: os dados chegam por `write` à medida que o núcleo lê o cartucho; saem em DATA de `block` bytes, cada um com ACK.
struct StreamOut : StreamSink {
  Session& s; uint8_t seq; uint16_t block, fill = 0; uint32_t off = 0, crc = 0; uint16_t fail = 0;
  StreamOut(Session& se, uint8_t sq, uint16_t b) : s(se), seq(sq), block(b) {}
  bool flush() {
    if (!fill) return true;
    uint8_t* tx = s.tx_;
    put_u32(tx + 6, off);
    crc = crc32_update(crc, tx + 10, fill);
    tx[0] = MAGIC0; tx[1] = MAGIC1; tx[2] = T_DATA; tx[3] = seq;
    put_u16(tx + 4, uint16_t(4 + fill));
    put_u32(tx + 6 + 4 + fill, crc32_update(0, tx + 2, 4 + 4 + fill));
    size_t frame = size_t(10) + 4 + fill;
    int r = 0;
    for (int t = 0; t < 4 && r == 0; t++) {
      s.io_.write(s.io_.ctx, tx, frame);
      r = s.wait_ack(seq, off, 400);
    }
    if (r <= 0) { fail = (r < 0) ? E_ABORTADO : E_REENVIOS; return false; }
    off += fill; fill = 0;
    return true;
  }
  bool write(const uint8_t* d, size_t n) override {
    if (fail) return false;
    while (n) {
      size_t room = block - fill, k = n < room ? n : room;
      memcpy(s.tx_ + 10 + fill, d, k);
      fill = uint16_t(fill + k); d += k; n -= k;
      if (fill == block && !flush()) return false;
    }
    return true;
  }
};

void Session::do_stream_read(uint8_t seq, uint8_t kind, uint8_t sys, uint16_t block) {
  uint8_t bp[7] = {kind, 0xFF, 0xFF, 0xFF, 0xFF, 0, 0};   // tamanho desconhecido
  put_u16(bp + 5, block);
  int r = 0;
  for (int t = 0; t < 4 && r == 0; t++) {
    send(T_BEGIN, seq, bp, 7);
    r = wait_ack(seq, 0, 500);
  }
  if (r <= 0) { send_error(seq, r < 0 ? E_ABORTADO : E_REENVIOS, "begin"); return; }
  StreamOut out(*this, seq, block);
  uint16_t err = E_CARTUCHO_IO;
  bool ok = be_.stream_read(sys, kind, out, err);
  if (ok && !out.flush()) ok = false;
  if (!ok) { send_error(seq, out.fail ? out.fail : err); return; }
  uint8_t ep[8];
  put_u32(ep, out.off); put_u32(ep + 4, out.crc);
  r = 0;
  for (int t = 0; t < 4 && r == 0; t++) {
    send(T_END, seq, ep, 8);
    r = wait_ack(seq, out.off, 500);
  }
  if (r <= 0) send_error(seq, r < 0 ? E_ABORTADO : E_REENVIOS, "end");
}

// PC -> dispositivo: o núcleo pede bytes com `read`; o ACK de cada bloco só sai depois que o núcleo consumiu o bloco inteiro,
// para o PC não mandar o próximo enquanto o cartucho ainda grava (o buffer da UART do AVR tem 64 bytes).
struct StreamIn : StreamSource {
  Session& s; uint8_t seq; uint32_t total, expected = 0, crc = 0; uint16_t cur_len = 0, cur_pos = 0; bool have = false, dead = false; uint32_t last_off = 0;
  StreamIn(Session& se, uint8_t sq, uint32_t size) : s(se), seq(sq), total(size) {}
  uint32_t size() const override { return total; }
  bool fetch() {
    uint32_t last = s.io_.now_ms(s.io_.ctx);
    while (s.io_.now_ms(s.io_.ctx) - last < 5000) {
      if (!s.next_frame(200)) continue;
      if (s.dec_.type == T_ABORT) { dead = true; return false; }
      if (s.dec_.seq != seq) continue;
      last = s.io_.now_ms(s.io_.ctx);
      if (s.dec_.type == T_H_DATA && s.dec_.len >= 4) {
        uint32_t off = get_u32(s.dec_.payload());
        uint16_t n = uint16_t(s.dec_.len - 4);
        if (off == expected && uint64_t(off) + n <= total) {
          crc = crc32_update(crc, s.dec_.payload() + 4, n);
          last_off = off; cur_len = n; cur_pos = 0; have = true; expected += n;
          return true;
        }
        if (off < expected) s.send_offset(T_D_ACK, seq, off);   // duplicado: confirma de novo
      }
    }
    dead = true;
    return false;
  }
  void ack() { if (have) { s.send_offset(T_D_ACK, seq, last_off); have = false; } }
  size_t read(uint8_t* d, size_t n) override {
    size_t got = 0;
    while (got < n && !dead) {
      if (!have || cur_pos == cur_len) {
        ack();
        if (expected >= total) break;
        if (!fetch()) break;
      }
      size_t k = cur_len - cur_pos; if (k > n - got) k = n - got;
      memcpy(d + got, s.dec_.payload() + 4 + cur_pos, k);
      cur_pos = uint16_t(cur_pos + k); got += k;
    }
    return got;
  }
};

void Session::do_stream_write(uint8_t seq, uint8_t sys, uint32_t size, uint8_t kind) {
  uint16_t err = E_CARTUCHO_IO;
  if (kind == KIND_ROM && !be_.rom_prepare(sys, size, err)) { send_error(seq, err); return; }   // conferir o chip e apagar: só depois o PC manda os dados
  send_offset(T_D_ACK, seq, 0);
  StreamIn in(*this, seq, size);
  bool ok = kind == KIND_ROM ? be_.stream_write_rom(sys, in, err) : be_.stream_write(sys, in, err);
  if (in.dead) { send_error(seq, E_REENVIOS, "timeout"); return; }
  if (!ok) { send_error(seq, err); return; }
  in.ack();                                              // confirma o último bloco, já consumido
  uint32_t last = io_.now_ms(io_.ctx);
  while (io_.now_ms(io_.ctx) - last < 5000) {
    if (!next_frame(200)) continue;
    if (dec_.type == T_ABORT) { send_offset(T_D_ACK, seq, 0); return; }
    if (dec_.seq != seq) continue;
    last = io_.now_ms(io_.ctx);
    if (dec_.type == T_H_END && dec_.len >= 8) {
      uint32_t t = get_u32(dec_.payload()), hcrc = get_u32(dec_.payload() + 4);
      if (t != size || in.expected != size || hcrc != in.crc) { send_error(seq, E_CRC); return; }
      send_offset(T_D_ACK, seq, t);
      return;
    }
    if (dec_.type == T_H_DATA && dec_.len >= 4) {        // bloco que o núcleo nem pediu (leu menos que o arquivo)
      send_error(seq, E_ARGUMENTO, "sobrou");
      return;
    }
  }
  send_error(seq, E_REENVIOS, "timeout");
}

}  // namespace oscr
