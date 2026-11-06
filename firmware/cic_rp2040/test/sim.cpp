// Simulador de PC: lock (snescic-lock-resync.hex) ligado a um key (snescic-key), ciclo a ciclo,
// pelo mesmo interpretador que roda no RP2040. Sem hardware, mostra se a autenticação do CIC fecha.
//
// Ligações (como no slot SNES):
//   rede 55 (dados 0): lock GP0 <-> key GP0
//   rede 24 (dados 1): lock GP1 <-> key GP1
//   rede 25 (reset do escravo): lock GP2 -> key GP2 (interrupção externa do key)
//   lock GP3 = reset de entrada (D40/PG1 do Mega); lock GP4 = reset do host (D41/PG0)
//   key GP4 = LED de estado (alto = autenticado; piscando = erro; baixo = sem CIC)
//
// Uso: sim <lock_prog.h gerado> não é lido em tempo de execução; os .hex são lidos direto:
//   sim lock.hex key.hex [região: 9 = D411, 6 = D413] [ciclos]
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include "../cic_rp2040/pic12f629.h"


// --- Referência independente: mangle() do sd2snes (cic/mangle.c), copiado aqui só para teste ---
#define CARRY if (a > 0x0f) { a &= 0xf; carry = 1; } else carry = 0;
static void refMangle(unsigned char* data) {
  unsigned char a, x, temp, offset, carry = 0;
  a = data[0xf];
  do {
    x = a; offset = 1; carry = 1;
    a += data[offset] + carry; data[offset] = a & 0xf; a = data[offset++];
    a += data[offset] + carry; a = (~a) & 0xf;
    temp = a; a = data[offset]; data[offset++] = temp & 0xf;
    a += data[offset] + carry;
    if (a < 0x10) { temp = a; a = data[offset]; data[offset++] = temp & 0xf; }
    a += data[offset]; data[offset] = a & 0xf; a = data[offset++];
    carry = 0; a += data[offset] + carry;
    temp = a; a = data[offset]; data[offset++] = temp & 0xf;
    a += 8;
    if (a < 0x10) a += data[offset] + carry;
    temp = a; a = data[offset]; data[offset++] = temp & 0xf;
    while (offset < 0x10) { a++; a += data[offset] + carry; data[offset] = a & 0xf; a = data[offset++]; }
    offset &= 0xf; a = x; a += 0xf; CARRY;
  } while (carry);
}

static bool loadHex(const char* path, uint16_t* words) {
  FILE* f = fopen(path, "r");
  if (!f) { perror(path); return false; }
  for (int i = 0; i < 1024; i++) words[i] = 0x3FFF;
  char line[600];
  unsigned ext = 0;
  while (fgets(line, sizeof line, f)) {
    if (line[0] != ':') continue;
    unsigned n, addr, typ;
    sscanf(line + 1, "%2x%4x%2x", &n, &addr, &typ);
    unsigned char d[300];
    for (unsigned i = 0; i < n; i++) { unsigned v; sscanf(line + 9 + 2 * i, "%2x", &v); d[i] = (unsigned char)v; }
    if (typ == 4) ext = ((d[0] << 8) | d[1]) << 16;
    if (typ == 0)
      for (unsigned i = 0; i + 1 < n; i += 2) {
        unsigned a = ext + addr + i;
        if (a < 0x800) words[a / 2] = (uint16_t)(d[i] | (d[i + 1] << 8));
      }
  }
  fclose(f);
  return true;
}

int main(int argc, char** argv) {
  if (argc < 3) { fprintf(stderr, "uso: sim lock.hex key.hex [regiao 9|6] [ciclos]\n"); return 2; }
  static uint16_t lockProg[1024], keyProg[1024];
  if (!loadHex(argv[1], lockProg) || !loadHex(argv[2], keyProg)) return 2;
  int region = argc > 3 ? atoi(argv[3]) : 9;
  long total = argc > 4 ? atol(argv[4]) : 3000000;

  cic::Pic12F629 lock(lockProg), key(keyProg);
  key.eeprom[0] = (uint8_t)region;

  int lockBusy = 0, keyBusy = 0;
  long contention = 0, ledEdges = 0, hostEdges = 0;
  int lastLed = 0, lastHost = 0;
  long lastLedChange = 0, lastHostChange = 0;
  const long kResetCycles = 200;
  // Oráculo dos seeds (rótulos no snescic-lock-resync.asm: main=0x20, fim dos 3 mangle=0xC2)
  unsigned char refLock[16], refKey[16];
  auto refInit = [&]() {
    static const unsigned char l[16] = {0, 0xb,1,4,0xf, 4,0xb,5,7, 0xf,0xd,6,1, 0xe,9,8};
    static const unsigned char k[16] = {0, 0xf,0,0xa,1, 8,5,0xf,1, 1,0xe,1,0, 0xd,0xe,0xc};
    memcpy(refLock, l, 16); memcpy(refKey, k, 16); refKey[2] = (unsigned char)region;
  };
  refInit();
  long rounds = 0, seedOk = 0, seedBad = 0;
  // Medição de ciclos por iteração dos loops de mangle. Contagem à mão no listing: 78 (sem skip) e 84 (com skip)
  // quando o loop repete, 76 e 82 quando retorna (-2). Os "69/73" nos comentários do .asm são antigos.
  long segStart = -1; int segKind = 0;          // 1 = loop do lock (0x16C), 2 = loop do key (0xDC)
  long hist[200] = {0}; long cyc = 0;       // o Mega segura PG1 alto no início e depois solta

  for (long t = 0; t < total; t++) {
    // 1) níveis das redes a partir do que cada lado dirige
    uint8_t ld = lock.drive(), ll = lock.level(), kd = key.drive(), kl = key.level();
    auto net = [&](int ln, int kn, int& level) {
      bool a = (ld >> ln) & 1, b = (kd >> kn) & 1;
      if (a && b && (((ll >> ln) & 1) != ((kl >> kn) & 1))) contention++;
      if (a) level = (ll >> ln) & 1;
      else if (b) level = (kl >> kn) & 1;
      else level = -1;   // solta
    };
    int n55, n24, n25;
    net(0, 0, n55); net(1, 1, n24); net(2, 2, n25);
    // pull-ups fracos do key (GP2 e GP5) e entradas soltas: leem 0 se ninguém dirige
    uint8_t lp = 0, kp = 0;
    auto put = [&](uint8_t& p, int bit, int lvl, int dflt) { if ((lvl < 0 ? dflt : lvl)) p |= (uint8_t)(1 << bit); };
    put(lp, 0, n55, 0); put(lp, 1, n24, 0); put(lp, 2, n25, 0);
    put(kp, 0, n55, 0); put(kp, 1, n24, 0);
    put(kp, 2, n25, (key.weakPullups() >> 2) & 1);
    if (t < kResetCycles) lp |= 0x08;                  // GP3 = PG1 alto: lock em reset
    lock.setPins(lp);
    key.setPins(kp);

    // 2) cada núcleo executa uma instrução quando termina a anterior
    if (lockBusy == 0) {
      uint16_t before = lock.pc();
      int c = lock.step();
      lockBusy = c - 1;
      uint16_t pcNow = lock.pc();
      if (pcNow == 0x020 && before != 0x020) { refInit(); }
      if (pcNow == 0x0C2) {                         // acabaram os 3 mangle de uma rodada
        for (int i = 0; i < 3; i++) { refMangle(refLock); refMangle(refKey); }
        bool same = true;
        for (int i = 1; i < 16; i++)
          if ((lock.gpr((uint8_t)(0x20 + i)) & 0xF) != refLock[i] || (lock.gpr((uint8_t)(0x30 + i)) & 0xF) != refKey[i]) same = false;   // o PIC não limpa o nibble alto
        rounds++; if (same) seedOk++; else { if (seedBad == 0) {
            printf("seed diverge na rodada %ld\n  ram lock:", rounds);
            for (int i = 1; i < 16; i++) printf(" %x", lock.gpr((uint8_t)(0x20 + i)));
            printf("\n  ref lock:"); for (int i = 1; i < 16; i++) printf(" %x", refLock[i]);
            printf("\n  ram key: "); for (int i = 1; i < 16; i++) printf(" %x", lock.gpr((uint8_t)(0x30 + i)));
            printf("\n  ref key: "); for (int i = 1; i < 16; i++) printf(" %x", refKey[i]);
            printf("\n"); } seedBad++; }
      }
      // fim de segmento (chegou a 0x169 = mangle_return, ou voltou ao início do loop) e início do próximo
      if (segKind && (pcNow == 0x169 || pcNow == 0x16C || pcNow == 0x0DC)) {
        long d = cyc + c - segStart; if (d >= 0 && d < 200) hist[d]++;
        segKind = 0;
      }
      if (pcNow == 0x16C) { segKind = 1; segStart = cyc + c; }
      if (pcNow == 0x0DC) { segKind = 2; segStart = cyc + c; }
      cyc += c;
    } else { lockBusy--; }
    if (keyBusy == 0) keyBusy = key.step() - 1; else keyBusy--;

    // 3) estatísticas
    int led = (key.level() >> 4) & 1;
    int host = (lock.level() >> 4) & 1;
    if (led != lastLed) { ledEdges++; lastLed = led; lastLedChange = t; }
    if (host != lastHost) { hostEdges++; lastHost = host; lastHostChange = t; }
  }

  printf("ciclos simulados: %ld (a 768 kHz = %.2f s)\n", total, total / 768000.0);
  printf("regiao do key (EEPROM[0]): %d\n", region);
  printf("conflitos de barramento: %ld\n", contention);
  printf("lock: reset do host (GP4) = %d, ultima mudanca no ciclo %ld, %ld mudancas\n",
         (lock.level() >> 4) & 1, lastHostChange, hostEdges);
  printf("key:  LED (GP4) = %d, ultima mudanca no ciclo %ld, %ld mudancas\n",
         (key.level() >> 4) & 1, lastLedChange, ledEdges);
  printf("pc do lock = 0x%03X, pc do key = 0x%03X\n", lock.pc(), key.pc());

  printf("rodadas de 3 mangle: %ld, seeds iguais ao mangle.c: %ld, diferentes: %ld\n", rounds, seedOk, seedBad);
  printf("ciclos por iteracao de mangle (esperado 76/78 e 82/84; 78 e 84 = loop repete, os \"CIC has 78/84\" do .asm):");
  long mangleTotal = 0, mangleOk = 0;
  for (int i = 0; i < 200; i++) if (hist[i]) { printf("  %d ciclos x %ld;", i, hist[i]); mangleTotal += hist[i]; if (i == 76 || i == 78 || i == 82 || i == 84) mangleOk += hist[i]; }
  printf("\n");
  bool oracleOk = rounds > 0 && seedBad == 0 && mangleTotal > 0 && mangleOk == mangleTotal;

  // Autenticação ok: sem conflito, host liberado, LED do key alto e estável na metade final.
  bool ok = contention == 0 && lastHost == 1 && lastLed == 1 &&
            lastLedChange < total / 2 && lastHostChange < total / 2 && oracleOk;
  printf("%s\n", ok ? "RESULTADO: AUTENTICACAO OK" : "RESULTADO: FALHOU");
  return ok ? 0 : 1;
}
