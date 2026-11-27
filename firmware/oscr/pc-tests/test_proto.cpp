// SPDX-License-Identifier: GPL-3.0-or-later
// Testes do firmware no PC: framing, CRC32 e sessão completa (modo MOCK).
// Compilar e rodar: make -C firmware/oscr/pc-tests test
#include <stdio.h>
#include <string.h>

#include <deque>
#include <vector>

#include "../src/dumper/oscr_proto.h"
#include "../src/dumper/oscr_session.h"

static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

using namespace oscr;

static void test_crc() {
  CHECK(crc32_update(0, (const uint8_t*)"123456789", 9) == 0xCBF43926u);
  CHECK(crc32_update(0, nullptr, 0) == 0u);
  CHECK(crc32_update(0, (const uint8_t*)"OSCR", 4) == 0xD2F82B80u);
  // incremental == de uma vez
  uint32_t a = crc32_update(0, (const uint8_t*)"1234", 4);
  CHECK(crc32_update(a, (const uint8_t*)"56789", 5) == 0xCBF43926u);
}

static void test_info_frame_bytes() {
  uint8_t out[16];
  size_t n = encode_frame(out, T_INFO, 1, nullptr, 0);
  const uint8_t want[] = {0xA5, 0x5A, 0x01, 0x01, 0x00, 0x00, 0x4E, 0xD2, 0x3A, 0x98};
  CHECK(n == sizeof want && memcmp(out, want, n) == 0);
}

static void test_decoder() {
  uint8_t buf[OSCR_MAX_PAYLOAD];
  Decoder d(buf, sizeof buf);
  std::vector<uint8_t> raw;
  uint8_t f1[1100], f2[1100];
  uint8_t pl[300];
  for (int i = 0; i < 300; i++) pl[i] = uint8_t(i);
  size_t n1 = encode_frame(f1, T_DATA, 7, pl, 300);
  size_t n2 = encode_frame(f2, T_INFO, 8, nullptr, 0);
  raw.push_back(0x00); raw.push_back(0xA5); raw.push_back(0xFF);   // lixo
  f1[10] ^= 0x01;                                                   // estraga o primeiro quadro
  raw.insert(raw.end(), f1, f1 + n1);
  raw.insert(raw.end(), f2, f2 + n2);
  int ok = 0;
  uint8_t last_seq = 0;
  for (uint8_t b : raw) if (d.push(b)) { ok++; last_seq = d.seq; }
  CHECK(ok == 1 && last_seq == 8 && d.bad == 1);
  // quadro válido de 1024
  uint8_t big[1024]; for (int i = 0; i < 1024; i++) big[i] = uint8_t(i * 3);
  static uint8_t fb[1100];
  size_t nb = encode_frame(fb, T_DATA, 9, big, 1024);
  int got = 0;
  for (size_t i = 0; i < nb; i++) if (d.push(fb[i])) got++;
  CHECK(got == 1 && d.len == 1024 && memcmp(d.payload(), big, 1024) == 0);
}

// ---- "host" em C++: responde dentro de Io::write, de forma determinística
struct Loop {
  std::deque<uint8_t> to_dev;                  // bytes que o dispositivo vai ler
  uint32_t now = 0;
  std::vector<uint8_t> file;                   // ROM/save reconstruído
  uint32_t expect = 0, crc = 0, total = 0, file_crc = 0;
  bool got_end = false, corrupt_first_data = false, drop_all_acks = false, got_err = false;
  uint16_t err_code = 0;
  uint8_t cur_seq = 1;
  std::vector<uint8_t> host_rx;
  Decoder dec;
  uint8_t dbuf[OSCR_MAX_PAYLOAD];
  Loop() : dec(dbuf, sizeof dbuf) {}

  void host_send(uint8_t type, const uint8_t* p, uint16_t len) {
    uint8_t out[1100];
    size_t n = encode_frame(out, type, cur_seq, p, len);
    for (size_t i = 0; i < n; i++) to_dev.push_back(out[i]);
  }
  void host_ack(uint8_t type, uint32_t off) {
    if (drop_all_acks) return;
    uint8_t p[4]; put_u32(p, off); host_send(type, p, 4);
  }
  void on_dev_byte(uint8_t b) {
    if (!dec.push(b)) return;
    if (dec.type == T_BEGIN) { host_ack(T_ACK, 0); file.clear(); expect = 0; }
    else if (dec.type == T_DATA) {
      uint32_t off = get_u32(dec.payload());
      if (off == expect) { file.insert(file.end(), dec.payload() + 4, dec.payload() + dec.len); expect += dec.len - 4; }
      host_ack(T_ACK, off);
    } else if (dec.type == T_ERRO) {
      got_err = true; err_code = get_u16(dec.payload());
    } else if (dec.type == T_END) {
      total = get_u32(dec.payload()); file_crc = get_u32(dec.payload() + 4); got_end = true;
      host_ack(T_ACK, total);
    }
  }
};

static int  lread(void* c, uint32_t to) {
  Loop* l = (Loop*)c;
  if (l->to_dev.empty()) { l->now += to ? to : 1; return -1; }
  uint8_t b = l->to_dev.front(); l->to_dev.pop_front(); return b;
}
static void lwrite(void* c, const uint8_t* d, size_t n) {
  Loop* l = (Loop*)c;
  if (l->corrupt_first_data && n > 20 && d[2] == T_DATA) {   // corrompe o 1º DATA só uma vez
    l->corrupt_first_data = false;
    std::vector<uint8_t> bad(d, d + n); bad[12] ^= 0xFF;
    for (uint8_t b : bad) l->on_dev_byte(b);
    return;
  }
  for (size_t i = 0; i < n; i++) l->on_dev_byte(d[i]);
}
static uint32_t lnow(void* c) { return ((Loop*)c)->now; }

static void test_session_dump(bool corrupt, bool drop) {
  Loop l; MockBackend be;
  static uint8_t rx[OSCR_MAX_PAYLOAD], tx[OSCR_MAX_PAYLOAD + 10];
  Session s(Io{&l, lread, lwrite, lnow}, be, rx, sizeof rx, tx, sizeof tx);
  l.corrupt_first_data = corrupt;
  uint8_t p[3] = {SYS_MOCK, 0, 0};
  l.host_send(T_DUMP_ROM, p, 3);
  if (drop) l.drop_all_acks = false;
  for (int i = 0; i < 200 && !l.got_end; i++) s.poll();
  CHECK(l.got_end);
  CHECK(l.file.size() == MockBackend::kRomSize);
  bool same = l.file.size() == MockBackend::kRomSize;
  for (uint32_t i = 0; same && i < l.file.size(); i++) same = l.file[i] == MockBackend::rom_byte(i);
  CHECK(same);
  CHECK(l.file_crc == crc32_update(0, l.file.data(), l.file.size()));
}

static void test_session_info_detect() {
  Loop l; MockBackend be;
  static uint8_t rx[OSCR_MAX_PAYLOAD], tx[OSCR_MAX_PAYLOAD + 10];
  Session s(Io{&l, lread, lwrite, lnow}, be, rx, sizeof rx, tx, sizeof tx);
  std::vector<uint8_t> out;
  struct Cap { static void w(void* c, const uint8_t* d, size_t n) { ((std::vector<uint8_t>*)c)->insert(((std::vector<uint8_t>*)c)->end(), d, d + n); } };
  // usa Io próprio que captura a saída
  struct C { Loop* l; std::vector<uint8_t>* o; };
  C c{&l, &out};
  Io io{&c, [](void* x, uint32_t t) { return lread(((C*)x)->l, t); },
        [](void* x, const uint8_t* d, size_t n) { Cap::w(((C*)x)->o, d, n); },
        [](void* x) { return lnow(((C*)x)->l); }};
  Session s2(io, be, rx, sizeof rx, tx, sizeof tx);
  l.cur_seq = 5; l.host_send(T_INFO, nullptr, 0);
  l.cur_seq = 6; uint8_t sys = SYS_MOCK; l.host_send(T_DETECT, &sys, 1);
  s2.poll(); s2.poll();
  uint8_t dbuf[64]; Decoder d(dbuf, sizeof dbuf);
  int frames = 0; bool info_ok = false, det_ok = false;
  for (uint8_t b : out) if (d.push(b)) {
    frames++;
    if (d.type == T_INFO_RESP && d.seq == 5 && d.len == 15 && get_u16(d.payload() + 7) == OSCR_MAX_PAYLOAD && d.payload()[0] == PROTO_VERSION && (d.payload()[4] & 1)) info_ok = true;
    if (d.type == T_DETECT_RESP && d.seq == 6 && d.payload()[1] == 0 && get_u32(d.payload() + 2) == MockBackend::kRomSize) det_ok = true;
  }
  CHECK(frames == 2 && info_ok && det_ok);
}

// ---- ERASE e opções no DETECT (programador de flash genérico)
struct EraseBackend : MockBackend {
  uint16_t o_chip = 0, o_prg = 0, o_chr = 0, erased_with = 0;
  bool supports(uint8_t s) override { return s == SYS_FLASH; }
  void set_options(uint16_t m, uint16_t p, uint16_t c) override { o_chip = m; o_prg = p; o_chr = c; }
  void detect(uint8_t, DetectInfo& o) override { o.status = 0; o.rom_size = uint32_t(o_prg) * 1024; o.save_size = 0; o.save_type = 0; strcpy(o.name, "ID C2F1"); }
  bool erase(uint8_t, uint16_t& err) override { if (o_chip == 9) { err = E_FLASH; return false; } erased_with = o_chip; return true; }
};

static void test_erase_e_detect_com_opcoes() {
  Loop l; EraseBackend be;
  static uint8_t rx[OSCR_MAX_PAYLOAD], tx[OSCR_MAX_PAYLOAD + 10];
  std::vector<uint8_t> out;
  struct C { Loop* l; std::vector<uint8_t>* o; };
  C c{&l, &out};
  Io io{&c, [](void* x, uint32_t t) { return lread(((C*)x)->l, t); },
        [](void* x, const uint8_t* d, size_t n) { ((C*)x)->o->insert(((C*)x)->o->end(), d, d + n); },
        [](void* x) { return lnow(((C*)x)->l); }};
  Session s(io, be, rx, sizeof rx, tx, sizeof tx);

  uint8_t det[7] = {SYS_FLASH, 3, 0, 0x00, 0x08, 5, 0};              // chip 3, prg 2048 KB, chr 5
  l.cur_seq = 1; l.host_send(T_DETECT, det, 7); s.poll();
  CHECK(be.o_chip == 0 || be.o_chip == 3);                            // as opções valem para um comando só (zeradas depois)
  uint8_t er[7] = {SYS_FLASH, 3, 0, 0, 4, 0, 0};
  l.cur_seq = 2; l.host_send(T_ERASE, er, 7); s.poll();
  CHECK(be.erased_with == 3);
  uint8_t bad[7] = {SYS_FLASH, 9, 0, 0, 4, 0, 0};
  l.cur_seq = 3; l.host_send(T_ERASE, bad, 7); s.poll();
  uint8_t other[7] = {SYS_SNES, 1, 0, 0, 4, 0, 0};
  l.cur_seq = 4; l.host_send(T_ERASE, other, 7); s.poll();
  l.cur_seq = 5; l.host_send(T_ERASE, er, 3); s.poll();               // curto demais

  uint8_t dbuf[128]; Decoder d(dbuf, sizeof dbuf);
  bool det_ok = false, ack2 = false, err3 = false, err4 = false, err5 = false;
  for (uint8_t b : out) if (d.push(b)) {
    if (d.type == T_DETECT_RESP && d.seq == 1 && d.payload()[1] == 0 && get_u32(d.payload() + 2) == 2048u * 1024) det_ok = true;
    if (d.type == T_D_ACK && d.seq == 2) ack2 = true;
    if (d.type == T_ERRO && d.seq == 3 && get_u16(d.payload()) == E_FLASH) err3 = true;
    if (d.type == T_ERRO && d.seq == 4 && get_u16(d.payload()) == E_SISTEMA) err4 = true;
    if (d.type == T_ERRO && d.seq == 5 && get_u16(d.payload()) == E_ARGUMENTO) err5 = true;
  }
  CHECK(det_ok && ack2 && err3 && err4 && err5);
  // F-1: ERASE avisa a etapa (seq 2 e 3) antes de bloquear; comando recusado antes do trabalho (seq 4 e 5) não avisa
  int st[6] = {0};
  Decoder d2(dbuf, sizeof dbuf);
  for (uint8_t b : out) if (d2.push(b) && d2.type == T_PROGRESSO && d2.len == 9 && d2.seq < 6 && d2.payload()[8] == STAGE_ERASE) st[d2.seq]++;
  CHECK(st[2] == 1 && st[3] == 1 && st[4] == 0 && st[5] == 0);
}

// ---- VOLT: seletor de tensão dos slots (D138); o 5V fica sempre ligado (D139)
struct VoltBackend : MockBackend {
  bool selector = false;
  uint64_t mask = 0;               // máscara de sistemas do INFO (D208: ids 16 a 31; D232: 32 a 63 no fim)
  uint64_t systems() override { return mask; }
  uint8_t volt = 1;                // 1 = 3,3 V, 2 = 5 V; a placa sobe em 3,3 V (estado seguro)
  bool chosen = false;
  int volt_calls = 0;
  bool supports(uint8_t s) override { return s == SYS_SNES || MockBackend::supports(s); }
  bool volt_select() override { return selector; }
  bool cart_voltage(uint8_t v, uint16_t& err) override { if (!selector) { err = E_COMANDO; return false; } volt_calls++; volt = v; chosen = v == 1; return true; }
  void volt_info(VoltInfo& p) override { p.select = selector; p.volt = selector ? volt : 0; p.chosen = chosen; }
};

struct VoltRun {
  Loop l; std::vector<uint8_t> out;
  struct C { Loop* l; std::vector<uint8_t>* o; } c;
  uint8_t rx[OSCR_MAX_PAYLOAD], tx[OSCR_MAX_PAYLOAD + 10];
  Io io; Session s;
  VoltRun(Backend& be) : c{&l, &out},
    io{&c, [](void* x, uint32_t t) { return lread(((C*)x)->l, t); },
       [](void* x, const uint8_t* d, size_t n) { ((C*)x)->o->insert(((C*)x)->o->end(), d, d + n); },
       [](void* x) { return lnow(((C*)x)->l); }},
    s(io, be, rx, sizeof rx, tx, sizeof tx) {}
  uint8_t seq = 0;
  uint8_t stage = 0xFF;   // etapa do último PROGRESSO que veio antes da resposta (0xFF = nenhum)
  // envia um comando e devolve o quadro de resposta (tipo e payload); os PROGRESSO (F-1) ficam em `stage`
  bool ask(uint8_t type, const uint8_t* pl, uint16_t n, uint8_t& rtype, std::vector<uint8_t>& rp) {
    out.clear(); seq++; stage = 0xFF; l.cur_seq = seq; l.host_send(type, pl, n); s.poll();
    uint8_t dbuf[128]; Decoder d(dbuf, sizeof dbuf);
    for (uint8_t b : out) if (d.push(b) && d.seq == seq) {
      if (d.type == T_PROGRESSO) { if (d.len == 9) stage = d.payload()[8]; continue; }
      rtype = d.type; rp.assign(d.payload(), d.payload() + d.len); return true;
    }
    return false;
  }
};

static void test_volt() {
  uint8_t t; std::vector<uint8_t> p;
  uint8_t st[1] = {VOLT_STATUS}, v3[1] = {VOLT_3V3}, v5[1] = {VOLT_5V}, bad[1] = {3}, det_snes[1] = {SYS_SNES};

  VoltBackend plain;                                                                              // placa sem seletor: 5 V fixo
  VoltRun q(plain);
  CHECK(q.ask(T_INFO, nullptr, 0, t, p) && t == T_INFO_RESP && !(p[4] & 32));
  plain.mask = (1ULL << 15) | (1ULL << 16) | (1ULL << 31);                                           // D208: bits 0..15 em u16 no offset 5, 16..31 em u16 no offset 9
  CHECK(q.ask(T_INFO, nullptr, 0, t, p) && p.size() == 15 && get_u16(p.data() + 5) == 0x8000 && get_u16(p.data() + 9) == 0x8001 && get_u32(p.data() + 11) == 0);
  plain.mask = (1ULL << 31) | (1ULL << 32) | (1ULL << 63);                                        // D232: bits 32..63 em u32 no offset 11
  CHECK(q.ask(T_INFO, nullptr, 0, t, p) && p.size() == 15 && get_u16(p.data() + 5) == 0 && get_u16(p.data() + 9) == 0x8000 && get_u32(p.data() + 11) == 0x80000001UL);
  plain.mask = 0;
  CHECK(q.ask(T_DETECT, det_snes, 1, t, p) && t == T_DETECT_RESP);                                // nada é recusado: o 5V está sempre ligado
  CHECK(q.ask(T_VOLT, st, 1, t, p) && t == T_VOLT_RESP && p.size() == 3 && p[0] == 0 && p[1] == 0 && p[2] == 0);
  CHECK(q.ask(T_VOLT, v3, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_COMANDO && plain.volt_calls == 0);   // sem seletor: não escolhe tensão
  CHECK(q.ask(T_VOLT, v5, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_COMANDO && plain.volt_calls == 0);
  CHECK(q.ask(T_VOLT, bad, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO);
  CHECK(q.ask(T_VOLT, nullptr, 0, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO);

  VoltBackend sel; sel.selector = true;                                                           // placa com o seletor 3,3 V/5 V
  VoltRun s2(sel);
  CHECK(s2.ask(T_INFO, nullptr, 0, t, p) && t == T_INFO_RESP && (p[4] & 32));                    // bit5: tem o seletor
  CHECK(s2.ask(T_VOLT, st, 1, t, p) && t == T_VOLT_RESP && p.size() == 3 && p[0] == 1 && p[1] == 1 && p[2] == 0 && sel.volt_calls == 0);   // status não mexe em nada; sobe em 3,3 V sem ninguém ter escolhido
  CHECK(s2.ask(T_VOLT, v3, 1, t, p) && t == T_VOLT_RESP && p[0] == 1 && p[1] == 1 && p[2] == 1 && sel.volt_calls == 1);   // escolhido pelo usuário
  CHECK(s2.ask(T_VOLT, v5, 1, t, p) && t == T_VOLT_RESP && p[0] == 1 && p[1] == 2 && p[2] == 0 && sel.volt_calls == 2);
  CHECK(s2.ask(T_DETECT, det_snes, 1, t, p) && t == T_DETECT_RESP);
  CHECK(s2.ask(T_VOLT, bad, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO);        // 3 e acima não existem
}

// ---- BOARD: perfil da placa guardado pelo PC (D162)
struct BoardBackend : MockBackend {
  bool supported = true, stored = false, selector = false;
  int sets = 0;
  bool volt_select() override { return selector; }
  bool board_supported() override { return supported; }
  bool board_get(uint8_t& f) override { f = selector ? BOARD_VOLT_SELECT : 0; return stored; }
  bool board_set(uint8_t f, uint16_t& err) override { if (!supported) { err = E_COMANDO; return false; } sets++; stored = true; selector = f & BOARD_VOLT_SELECT; return true; }
};

static void test_board() {
  uint8_t t; std::vector<uint8_t> p;
  uint8_t st[1] = {BOARD_STATUS}, set_v[2] = {BOARD_SET, BOARD_VOLT_SELECT}, set_n[2] = {BOARD_SET, 0}, bad_act[1] = {2}, bad_bits[2] = {BOARD_SET, 2}, short_set[1] = {BOARD_SET};

  BoardBackend none; none.supported = false;                                                       // backend sem perfil: INFO sem bit7, comando recusado
  VoltRun q(none);
  CHECK(q.ask(T_INFO, nullptr, 0, t, p) && t == T_INFO_RESP && !(p[4] & 128));
  CHECK(q.ask(T_BOARD, st, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_COMANDO);

  BoardBackend b;                                                                                  // backend com perfil
  VoltRun s(b);
  CHECK(s.ask(T_INFO, nullptr, 0, t, p) && t == T_INFO_RESP && (p[4] & 128) && !(p[4] & 32) && p[2] == 2);   // bit7: tem BOARD; sem seletor; firmware 0.2
  CHECK(s.ask(T_BOARD, st, 1, t, p) && t == T_BOARD_RESP && p.size() == 2 && p[0] == 0 && p[1] == 0 && b.sets == 0);   // consulta: nada guardado, nada muda
  CHECK(s.ask(T_BOARD, set_v, 2, t, p) && t == T_BOARD_RESP && p[0] == 1 && p[1] == BOARD_VOLT_SELECT && b.sets == 1);   // grava: placa com seletor
  CHECK(s.ask(T_INFO, nullptr, 0, t, p) && t == T_INFO_RESP && (p[4] & 32));                    // o INFO já mostra o seletor (bit5)
  CHECK(s.ask(T_BOARD, st, 1, t, p) && t == T_BOARD_RESP && p[0] == 1 && p[1] == BOARD_VOLT_SELECT && b.sets == 1);
  CHECK(s.ask(T_BOARD, set_n, 2, t, p) && t == T_BOARD_RESP && p[0] == 1 && p[1] == 0 && b.sets == 2);   // volta para a placa sem seletor
  CHECK(s.ask(T_INFO, nullptr, 0, t, p) && t == T_INFO_RESP && !(p[4] & 32));
  CHECK(s.ask(T_BOARD, bad_act, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO && b.sets == 2);   // ação desconhecida
  CHECK(s.ask(T_BOARD, bad_bits, 2, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO && b.sets == 2);  // bit de perfil que não existe: recusa sem gravar
  CHECK(s.ask(T_BOARD, short_set, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO && b.sets == 2); // gravação sem os flags
  CHECK(s.ask(T_BOARD, nullptr, 0, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO);
}

// ---- SELFTEST: autoteste da placa sem cartucho (P-12)
struct SelfBackend : MockBackend {
  bool supported = true, fail = false;
  int items = 0;                                    // quantos achados o teste simulado devolve
  int calls = 0;
  bool selftest_supported() override { return supported; }
  bool selftest(SelfTestReport& r, uint16_t& err) override {
    calls++;
    if (fail) { err = E_CARTUCHO_IO; return false; }
    for (int i = 0; i < items; i++) r.add(i == 0 ? ST_GND : ST_PAIR, uint8_t(22 + i), i == 0 ? 0 : uint8_t(54 + i));
    return true;
  }
};

static void test_selftest() {
  uint8_t t; std::vector<uint8_t> p;
  SelfBackend none; none.supported = false;                                                       // firmware sem o núcleo: INFO sem bit6, comando recusado
  VoltRun q(none);
  CHECK(q.ask(T_INFO, nullptr, 0, t, p) && t == T_INFO_RESP && !(p[4] & 64));
  CHECK(q.ask(T_SELFTEST, nullptr, 0, t, p) && t == T_ERRO && get_u16(p.data()) == E_COMANDO && none.calls == 0);

  SelfBackend ok;                                                                                 // tudo certo: resposta vazia
  VoltRun s(ok);
  CHECK(s.ask(T_INFO, nullptr, 0, t, p) && t == T_INFO_RESP && (p[4] & 64));
  CHECK(s.ask(T_SELFTEST, nullptr, 0, t, p) && t == T_SELFTEST_RESP && p.size() == 2 && p[0] == 0 && p[1] == 0 && ok.calls == 1);
  CHECK(s.stage == STAGE_SELFTEST);                                                               // F-1: avisa a etapa antes do trabalho longo

  SelfBackend bad; bad.items = 3;                                                                 // três achados: GND no pino 22 e dois pares
  VoltRun b(bad);
  CHECK(b.ask(T_SELFTEST, nullptr, 0, t, p) && t == T_SELFTEST_RESP && p.size() == 2 + 9 && p[0] == 0 && p[1] == 3);
  CHECK(p[2] == ST_GND && p[3] == 22 && p[4] == 0 && p[5] == ST_PAIR && p[6] == 23 && p[7] == 55 && p[8] == ST_PAIR && p[9] == 24 && p[10] == 56);

  SelfBackend many; many.items = 40;                                                              // acima do limite: corta em 24 e avisa
  VoltRun m(many);
  CHECK(m.ask(T_SELFTEST, nullptr, 0, t, p) && t == T_SELFTEST_RESP && p.size() == 2 + SelfTestReport::kMax * 3 && p[0] == 1 && p[1] == SelfTestReport::kMax);

  SelfBackend ioerr; ioerr.fail = true;                                                           // o núcleo falhou: ERRO
  VoltRun e(ioerr);
  CHECK(e.ask(T_SELFTEST, nullptr, 0, t, p) && t == T_ERRO && get_u16(p.data()) == E_CARTUCHO_IO);
}

// ---- CLOCK: relógio do Si5351 (F-3)
struct ClockBackend : MockBackend {
  bool present = true, stored = false, test = false;
  int32_t ppb = 0;
  int sets = 0;
  bool clock_supported() override { return true; }
  bool clock(uint8_t action, int32_t v, ClockInfo& out, uint16_t& err) override {
    if (action != CLOCK_STATUS && !present) { err = E_CARTUCHO_IO; return false; }
    if (action == CLOCK_SET) { ppb = v; stored = true; sets++; }
    if (action == CLOCK_TEST_ON) test = true;
    if (action == CLOCK_TEST_OFF) test = false;
    out.present = present; out.stored = stored; out.ppb = ppb; out.test = test;
    return true;
  }
};

static void test_clock() {
  uint8_t t; std::vector<uint8_t> p;
  uint8_t st[1] = {CLOCK_STATUS}, on[1] = {CLOCK_TEST_ON}, off[1] = {CLOCK_TEST_OFF}, bad[1] = {9};
  uint8_t set[5] = {CLOCK_SET, 0, 0, 0, 0};
  put_u32(set + 1, uint32_t(int32_t(-1234)));

  VoltRun plain(*new MockBackend);                                                                // firmware sem o comando: ERRO comando (host acusa "firmware antigo")
  CHECK(plain.ask(T_CLOCK, st, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_COMANDO);

  ClockBackend be;
  VoltRun r(be);
  CHECK(r.ask(T_CLOCK, st, 1, t, p) && t == T_CLOCK_RESP && p.size() == 7 && p[0] == 1 && p[1] == 0 && get_u32(p.data() + 2) == 0 && p[6] == 0);
  CHECK(r.ask(T_CLOCK, set, 5, t, p) && t == T_CLOCK_RESP && p[1] == 1 && int32_t(get_u32(p.data() + 2)) == -1234 && be.sets == 1);   // fator negativo volta com sinal
  CHECK(r.ask(T_CLOCK, on, 1, t, p) && t == T_CLOCK_RESP && p[6] == 1);
  CHECK(r.ask(T_CLOCK, off, 1, t, p) && t == T_CLOCK_RESP && p[6] == 0);
  CHECK(r.ask(T_CLOCK, bad, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO);
  CHECK(r.ask(T_CLOCK, nullptr, 0, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO);
  CHECK(r.ask(T_CLOCK, set, 3, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO);        // SET sem o fator inteiro
  uint8_t big[5] = {CLOCK_SET, 0, 0, 0, 0};
  put_u32(big + 1, uint32_t(CLOCK_MAX_PPB + 1));
  CHECK(r.ask(T_CLOCK, big, 5, t, p) && t == T_ERRO && get_u16(p.data()) == E_ARGUMENTO && be.sets == 1);   // acima do limite: não chega ao backend
  put_u32(big + 1, uint32_t(-CLOCK_MAX_PPB));
  CHECK(r.ask(T_CLOCK, big, 5, t, p) && t == T_CLOCK_RESP && be.sets == 2);                       // o limite em si vale

  ClockBackend none; none.present = false;                                                        // sem o módulo: consulta responde, o resto dá erro
  VoltRun n(none);
  CHECK(n.ask(T_CLOCK, st, 1, t, p) && t == T_CLOCK_RESP && p[0] == 0);
  CHECK(n.ask(T_CLOCK, set, 5, t, p) && t == T_ERRO && get_u16(p.data()) == E_CARTUCHO_IO && none.sets == 0);
  CHECK(n.ask(T_CLOCK, on, 1, t, p) && t == T_ERRO && get_u16(p.data()) == E_CARTUCHO_IO);
}

int main() {
  test_crc();
  test_info_frame_bytes();
  test_decoder();
  test_session_dump(false, false);
  test_session_dump(true, false);    // 1º DATA corrompido: o dispositivo reenvia
  test_session_info_detect();
  test_erase_e_detect_com_opcoes();
  test_volt();
  test_board();
  test_selftest();
  test_clock();
  printf("%d verificações, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
