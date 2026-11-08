// SPDX-License-Identifier: GPL-3.0-or-later
// Fork oscr_minimal: laço de comandos do protocolo serial (docs/referencia/protocolo.md) ligado aos núcleos do OSCR.
// Estado: SNES, NES/Famicom, Mega Drive, GBA e GB/GBC (DETECT, DUMP_ROM, READ_SAVE e WRITE_SAVE), nunca rodados em hardware (docs/referencia/fork-oscr.md).
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER

# include <setjmp.h>

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "ui.h"
# include "cores/include.h"
# include "cores/MegaDrive.h"
# include "cores/GameBoyAdvance.h"
# include "cores/GameBoy.h"
# include "cores/SNES.h"
# include "cores/NES.h"
# include "dumper/Dumper.h"
# include "dumper/NesFlash.h"
# include "dumper/SnesFlash.h"
# include "dumper/MdFlash.h"
# include "dumper/GbaFlash.h"
# include "dumper/GbFlash.h"
# include "dumper/FlashProg.h"
# include "dumper/PowerCore.h"

// `mmc6` e `flashfound` ficam no .cpp do núcleo NES, sem declaração no cabeçalho; o MMC6 só é marcado, nunca desmarcado.
namespace OSCR::Cores::NES { extern bool mmc6; extern bool flashfound; }

# ifndef OSCR_DUMPER_BAUD
#   define OSCR_DUMPER_BAUD 1000000UL     // 115200 como fallback: compile com -DOSCR_DUMPER_BAUD=115200
# endif

namespace OSCR::Dumper
{
  namespace
  {
    oscr::StreamSink * activeSink = nullptr;
    oscr::StreamSource * activeSource = nullptr;
    bool errorFlag = false;
    jmp_buf escape;
    bool armed = false;

    uint8_t rxBuf[OSCR_MAX_PAYLOAD];
    uint8_t txBuf[OSCR_MAX_PAYLOAD + 10];

    int ioRead(void *, uint32_t timeoutMs)
    {
      uint32_t start = millis();
      for (;;)
      {
        if (ClockedSerial.available()) return ClockedSerial.read();
        if (millis() - start >= timeoutMs) return -1;
      }
    }

    void ioWrite(void *, uint8_t const * data, size_t len)
    {
      ClockedSerial.rawWrite(data, len);     // a UI de texto fica muda; só o protocolo usa a serial
    }

    uint32_t ioNow(void *) { return millis(); }

    /**
     * `/CART` do Mega Drive (B32 -> D50 = PB3, placa 16_bits v. 1.2; D87): o cartucho liga o pino ao GND, então baixo = há cartucho.
     * Alto não diz nada: placas anteriores deixam o pino solto e o pull-up interno lê alto, e com a v. 1.2 alto também é "slot vazio".
     * Por isso só o nível baixo é usado (como prova de que há cartucho). Nenhum núcleo do OSCR usa PB3 neste fork; o estado anterior do pino é restaurado.
     */
    bool mdCartPinLow()
    {
      uint8_t const bit = _BV(PB3);
      uint8_t const ddr = DDRB & bit, port = PORTB & bit;
      DDRB &= ~bit;
      PORTB |= bit;
      delayMicroseconds(50);                      // o pull-up interno (cerca de 35 kΩ) carrega o fio de 25 mm e os 5 pF do cartucho em poucos microssegundos
      bool low = (PINB & bit) == 0;
      PORTB = (PORTB & ~bit) | port;
      DDRB = (DDRB & ~bit) | ddr;
      return low;
    }

    /**
     * Executa uma função de núcleo com a saída ligada ao fluxo. Erros fatais dos núcleos (UI::fatalError) voltam aqui por longjmp.
     * Devolve false se o núcleo falhou.
     */
    bool fatalHit = false;
    bool abortHit = false;

    template <typename Fn>
    bool runCore(Fn fn, bool softErrors = false)
    {
      errorFlag = false;
      fatalHit = false;
      abortHit = false;
      armed = true;
      bool ok = true;

      if (setjmp(escape) == 0)
      {
        fn();
      }
      else
      {
        ok = false;
        fatalHit = true;
      }

      armed = false;
      OSCR::Power::disableCartridge();
      OSCR::Storage::Shared::sharedFile.close();
      return ok && (softErrors || !errorFlag);
    }

    /** Repassa ao fluxo do protocolo contando os bytes: erros "suaves" do OSCR depois de o dado sair não derrubam o comando. */
    struct CountingSink : oscr::StreamSink
    {
      oscr::StreamSink * inner = nullptr;
      uint32_t bytes = 0;
      bool write(uint8_t const * data, size_t len) override { bytes += len; return inner->write(data, len); }
    };

    struct CountingSource : oscr::StreamSource
    {
      oscr::StreamSource * inner = nullptr;
      uint32_t bytes = 0;
      size_t read(uint8_t * data, size_t len) override { size_t n = inner->read(data, len); bytes += n; return n; }
      uint32_t size() const override { return inner->size(); }
    };

    CountingSink countingSink;
    CountingSource countingSource;

    namespace MD = OSCR::Cores::MegaDrive;
    namespace GBA = OSCR::Cores::GameBoyAdvance;
    namespace GB = OSCR::Cores::GameBoy;
    namespace SN = OSCR::Cores::SNES;

    /**
     * GBA sem a base de dados do OSCR: lê o cabeçalho, confere o logo da Nintendo e o checksum e acha o tamanho da ROM pelo espelhamento
     * (o menor deslocamento em que a ROM se repete; sem espelho até 16 MB, 32 MB). O tipo de save vem do usuário (campo `mapper`).
     * Devolve 0 = ok, 1 = sem cartucho, 4 = há dados mas o checksum do cabeçalho não confere.
     */
    uint8_t gbaProbe(uint8_t saveOption)
    {
      using namespace OSCR::Cores;
      uint8_t * buf = OSCR::Storage::Shared::buffer;

      GBA::cartOn();
      for (uint16_t w = 0; w < 192; w += 2)
      {
        uint16_t word = GBA::readWord(w);
        buf[w] = word & 0xFF;
        buf[w + 1] = word >> 8;
      }

      uint32_t size = 32UL << 20;
      for (uint32_t cand = 256UL << 10; cand <= (16UL << 20); cand <<= 1)
      {
        bool mirror = true;
        for (uint8_t i = 0; i < 64 && mirror; i += 2) mirror = GBA::readWord(cand + i) == GBA::readWord(i);
        if (mirror) { size = cand; break; }
      }
      GBA::cartOff();

      uint16_t logo = 0;
      for (uint8_t i = 0x04; i < 0xA0; i++) logo += buf[i];
      if (logo != 0x4B1B) return 1;

      cartID[0] = char(buf[0xAC]); cartID[1] = char(buf[0xAD]); cartID[2] = char(buf[0xAE]); cartID[3] = char(buf[0xAF]); cartID[4] = 0;
      setOutName(reinterpret_cast<char const *>(&buf[0xA0]), 12);
      romVersion = buf[0xBC];
      checksum = GBA::checksumHeader(buf);
      cartSize = size;
      saveType = saveOption ? saveOption : 3;     // sem informação: SRAM/FRAM de 32 KB, como no firmware próprio

      return buf[0xBD] == checksum ? 0 : 4;
    }

    uint32_t gbaSaveBytes(uint8_t type)
    {
      static uint32_t const sizes[] = {0, 512, 8192, 32768, 65536, 131072, 65536};   // numeração do OSCR: 1 4K EEPROM, 2 64K EEPROM, 3 SRAM 32K, 4 Flash 64K, 5 Flash 128K, 6 SRAM 64K
      return type < sizeof sizes / sizeof sizes[0] ? sizes[type] : 0;
    }

    /**
     * Game Boy / Game Boy Color: o `checkCart` do OSCR lê o cabeçalho e preenche romType, romBanks, sramBanks e lastByteAddress.
     * Devolve 0 = ok, 1 = sem cartucho, 4 = há dados mas o checksum do cabeçalho não confere (o "continuar" do OSCR não existe aqui).
     */
    uint8_t gbProbe()
    {
      if (GB::checkCart()) return 0;
      uint8_t const * h = &OSCR::Storage::Shared::buffer[0x100];
      for (uint8_t i = 1; i < 0x50; i++) if (h[i] != h[0]) return 4;
      return 1;
    }

    /** Bytes do save lido por `GB::readSave()`, pela mesma conta das funções do OSCR (0 = sem save). */
    uint32_t gbSaveBytes()
    {
      using namespace OSCR::Cores;
      if (!GB::lastByteAddress) return 0;
      if (romType == 0x22) return GB::lastByteAddress;                      // MBC7: 256 ou 512 bytes (guardados como tamanho, não endereço)
      if (romType == 0x20) return 32768UL + 1048576UL;                      // MBC6: SRAM de 32 KB + Flash de 1 MB
      return uint32_t(GB::sramBanks) * (uint32_t(GB::lastByteAddress) - 0xA000UL + 1UL);
    }

    /**
     * Chave de 5V dos slots em software (D108, D116; sem chave física, D123). D19 = PD2, nível baixo liga o P-MOSFET Q1; com o pino solto (Mega em reset) o R16 mantém
     * a chave desligada. Em placas sem a chave o pino fica sem ligação e isto não tem efeito.
     *  OSCR_POWER_SWITCH     1 = placa com a chave de 5V: o firmware começa desligado e o host liga (POWER).
     *  OSCR_POWER_SENSE      1 = sensor do rail no D53 (PB0, nó do Q3): nível alto = rail baixo = seguro trocar.
     *  OSCR_POWER_DISCHARGE  1 = transistor de descarga (Q2): a espera depois de cortar cai de 2 s para 0,5 s.
     */
    void cartPower(bool on)
    {
      DDRD |= _BV(PD2);
      if (on) PORTD &= ~_BV(PD2);
      else PORTD |= _BV(PD2);
    }

#ifndef OSCR_POWER_SWITCH
# define OSCR_POWER_SWITCH 0
#endif
#ifndef OSCR_POWER_SENSE
# define OSCR_POWER_SENSE 0
#endif
#ifndef OSCR_POWER_DISCHARGE
# define OSCR_POWER_DISCHARGE 0
#endif
#ifndef OSCR_POWER_DISCHARGE_MS
# define OSCR_POWER_DISCHARGE_MS (OSCR_POWER_DISCHARGE ? 500 : 2000)   // espera depois de cortar o 5V sem sensor
#endif
#ifndef OSCR_POWER_CYCLE_TRIES
# define OSCR_POWER_CYCLE_TRIES 3                                       // SA-1: tentativas de ler o cabeçalho, com ciclo de energia entre elas
#endif
    constexpr bool kPowerSwitch = OSCR_POWER_SWITCH;

    /** Solta todos os pinos de sinal dos slots (entrada, sem pull-up). Cortar o 5V com o Mega ainda dirigindo os pinos alimentaria o cartucho por eles.
     *  Não toca na serial (PE0/PE1), no I²C (PD0/PD1), em D19 (PD2), no sensor (PB0) nem nos LEDs (PB4 a PB7). */
    void releaseCartPins()
    {
      DDRA = 0; PORTA = 0;                      // D22 a D29
      DDRC = 0; PORTC = 0;                      // D30 a D37
      DDRF = 0; PORTF = 0;                      // A0 a A7
      DDRK = 0; PORTK = 0;                      // A8 a A15
      DDRL = 0; PORTL = 0;                      // D42 a D49
      DDRE &= ~(_BV(PE3) | _BV(PE4) | _BV(PE5)); PORTE &= ~(_BV(PE3) | _BV(PE4) | _BV(PE5));                 // D5, D2, D3
      DDRG &= ~(_BV(PG0) | _BV(PG1) | _BV(PG2) | _BV(PG5)); PORTG &= ~(_BV(PG0) | _BV(PG1) | _BV(PG2) | _BV(PG5));   // D41, D40, D39, D4
      DDRH &= ~(_BV(PH0) | _BV(PH1) | _BV(PH3) | _BV(PH4) | _BV(PH5) | _BV(PH6));
      PORTH &= ~(_BV(PH0) | _BV(PH1) | _BV(PH3) | _BV(PH4) | _BV(PH5) | _BV(PH6));                            // D17, D16, D6, D7, D8, D9
      DDRJ &= ~(_BV(PJ0) | _BV(PJ1)); PORTJ &= ~(_BV(PJ0) | _BV(PJ1));                                         // D15, D14
      DDRD &= ~_BV(PD7); PORTD &= ~_BV(PD7);                                                                    // D38
      DDRB &= ~_BV(PB3); PORTB &= ~_BV(PB3);                                                                    // D50 (/CART), sem pull-up
    }

    bool powerOn = true;

    bool railLow() { return (PINB & _BV(PB0)) != 0; }          // sensor do Q3: alto = rail baixo

    /** 1) solta os barramentos  2) abre o Q1  3) espera a descarga (o sensor, se houver; senão o tempo fixo). */
    void railDown()
    {
      releaseCartPins();
      cartPower(false);
      oscr::power::wait_discharge(OSCR_POWER_SENSE != 0, 500, OSCR_POWER_DISCHARGE_MS, [] { return railLow(); }, [](uint32_t ms) { delay(ms); }, [] { return uint32_t(millis()); });
    }

    void railUp()
    {
      cartPower(true);                          // 5V primeiro; os núcleos reconfiguram os pinos no próximo comando de leitura
      delay(50);                                // 5V, Si5351 e PIC estabilizam
    }

    uint8_t probeAttempts = 1;                  // SNES: leituras do cabeçalho feitas no último `snesProbe` (> 1 = usou o ciclo de energia do SA-1)

    /**
     * SNES: o `getCartInfo` do OSCR lê o cabeçalho ($FFB0) e preenche romSize (Mbit), numBanks, sramSize (Kbit), romChips, romType e checksum
     * (sem a base de dados: tamanhos fora do padrão, como 6 MB, vêm do PC pela opção `prg_kb`). `sizeKb` > 0 troca o tamanho da ROM.
     * Devolve 0 = ok, 1 = sem cartucho, 4 = há dados mas o cabeçalho não confere.
     */
    uint8_t snesProbe(uint16_t sizeKb)
    {
      using namespace OSCR::Cores;
      // SA-1: o destravamento falha de vez em quando (clock, tensão, capacitores ainda carregados). Com a chave de 5V (kPowerSwitch) a leitura do
      // cabeçalho se repete até OSCR_POWER_CYCLE_TRIES vezes, desligando e ligando o 5V entre as tentativas (D119).
      auto attempt = []() -> bool
      {
        abortHit = false;
        checksum = 0; romSize = 0; numBanks = 0; sramSize = 0;
        SN::getCartInfo();
        SN::cartOff();
        return !abortHit;
      };
      bool ok = false;
      if (kPowerSwitch && powerOn) probeAttempts = oscr::power::retry_with_cycle(OSCR_POWER_CYCLE_TRIES, attempt, [] { railDown(); railUp(); }, ok);
      else { probeAttempts = 1; ok = attempt(); }
      (void)ok;
      if (abortHit) return (checksum == 0 || checksum == 0xFFFF) ? 1 : 4;
      if (romSize == 0 || numBanks < 1) return 1;

      if (sizeKb)                                                 // tamanho informado pelo usuário/PC (Mbit = KB / 128)
      {
        romSize = sizeKb / 128;
        constexpr uint8_t kSA = 3, kEX = 4;
        numBanks = (romType == kEX || romType == kSA) ? long(romSize) * 2 : (long(romSize) * 1024 * 1024 / 8) / (32768 + (long(romType) * 32768));
      }
      return 0;
    }


    namespace NE = OSCR::Cores::NES;

    NE::crdbNESRecord nesRec;                       // no lugar do registro da base de dados: os macros NES_* do núcleo apontam para cá
    uint32_t nesPrgBytes = 0, nesChrBytes = 0, nesRamBytes = 0;
    char nesName[24];

    bool isNes(uint8_t system) { return system == oscr::SYS_NES || system == oscr::SYS_FAMICOM; }

    bool allSame(uint8_t const * p, uint8_t n) { for (uint8_t i = 1; i < n; i++) if (p[i] != p[0]) return false; return true; }

    uint8_t log2u(uint16_t v) { uint8_t n = 0; while (v > 1) { v >>= 1; n++; } return n; }

    bool isPow2(uint16_t v) { return v != 0 && (v & (v - 1)) == 0; }

    /** Mapper com PRG-RAM aceita em READ_SAVE/WRITE_SAVE (o mesmo conjunto do firmware próprio). */
    bool nesHasSave(uint16_t m) { return m == 1 || m == 4 || m == 5 || m == 69 || m == 118; }

    /**
     * Confere mapper e tamanhos de ROM (KB) contra os limites do protocolo (docs/referencia/protocolo.md, NES/Famicom).
     * Devolve 0 = ok, E_SISTEMA = mapper ou tamanho além do registrador, E_ARGUMENTO = tamanhos inválidos.
     */
    uint16_t nesCheckRom(uint16_t m, uint16_t prg, uint16_t chr)
    {
      bool known = m == 0 || m == 1 || m == 2 || m == 3 || m == 4 || m == 5 || m == 7 || m == 9 || m == 10 || m == 11 || m == 33 || m == 48 || m == 66 || m == 69 || m == 70 || m == 71
                   || m == 75 || m == 78 || m == 79 || m == 87 || m == 118 || m == 206
                   || m == 13 || m == 30 || m == 34 || m == 67 || m == 68 || m == 72 || m == 73 || m == 86 || m == 92 || m == 93 || m == 94 || m == 140 || m == 152 || m == 180 || m == 184;
      if (!known) return oscr::E_SISTEMA;
      // O núcleo do OSCR conta bancos em potências de 2 (NES_PRG e NES_CHR são expoentes).
      if (prg == 0 || prg % 16 != 0 || chr % 8 != 0 || !isPow2(prg / 16) || (chr && !isPow2(chr / 8))) return oscr::E_ARGUMENTO;
      if ((m == 2 || m == 7 || m == 71 || m == 13 || m == 30 || m == 73 || m == 93 || m == 94 || m == 180) && chr != 0) return oscr::E_ARGUMENTO;     // CHR-RAM
      if ((m == 79 || m == 87 || m == 78 || m == 75 || m == 70 || m == 33 || m == 48 || m == 118 || m == 206 || m == 67 || m == 68 || m == 72 || m == 92 || m == 86 || m == 140 || m == 152 || m == 184) && chr == 0) return oscr::E_ARGUMENTO;   // CHR-ROM
      if ((m == 7 || m == 11 || m == 66 || m == 79 || m == 34 || m == 86 || m == 140 || m == 13) && prg % 32 != 0) return oscr::E_ARGUMENTO;
      if (((m == 0 || m == 3) && prg > 32) || (m == 1 && (prg > 256 || chr > 128)) || (m == 4 && (prg > 512 || chr > 256)) || ((m == 9 || m == 10) && chr > 128) || (m == 69 && chr > 256)) return oscr::E_SISTEMA;
      if ((m == 9 && prg > 128) || (m == 10 && prg > 256) || (m == 11 && (prg > 128 || chr > 128))
          || (m == 66 && (prg > 128 || chr > 32)) || (m == 69 && prg > 512) || (m == 5 && prg > 1024)
          || ((m == 33 || m == 48) && (prg > 256 || chr > 256)) || (m == 70 && (prg > 256 || chr > 128)) || (m == 75 && (prg > 128 || chr > 128))
          || (m == 78 && (prg > 128 || chr > 128)) || (m == 79 && (prg > 64 || chr > 64)) || (m == 87 && (prg > 32 || chr > 32))
          || (m == 118 && (prg > 512 || chr > 256)) || (m == 206 && (prg > 128 || chr > 64))
          || (m == 30 && prg > 512) || (m == 13 && prg > 32) || (m == 34 && (prg > 512 || chr > 64)) || (m == 67 && (prg > 128 || chr > 128)) || (m == 68 && (prg > 256 || chr > 256))
          || (m == 72 && (prg > 128 || chr > 128)) || (m == 92 && (prg > 256 || chr > 128)) || (m == 73 && prg > 128) || (m == 86 && (prg > 128 || chr > 64))
          || ((m == 93 || m == 94 || m == 180) && prg > 128) || (m == 140 && (prg > 128 || chr > 128)) || (m == 152 && (prg > 128 || chr > 128))
          || (m == 184 && (prg > 32 || chr > 32))) return oscr::E_SISTEMA;
      return 0;
    }

    /**
     * NES/Famicom: o cartucho não tem cabeçalho, então mapper e tamanhos vêm do PC (sem a base de dados do OSCR).
     * `mapper` 0 e `prgKb` 0 = automático (NROM: 16 ou 32 KB pelo espelhamento). Em modo save, `prgKb` é a RAM em KB (0 = 8).
     * Monta o registro do núcleo (`nesRec`, com o cabeçalho iNES sintético) e confere o MMC6. Deve rodar dentro de `runCore`.
     * Devolve 0 = ok, ou o código de erro do protocolo (E_SEM_CARTUCHO, E_SISTEMA, E_ARGUMENTO, E_SEM_SAVE).
     */
    uint16_t nesProbe(bool forSave, uint16_t m, uint16_t prgKb, uint16_t chrKb)
    {
      using namespace OSCR::Cores;
      uint8_t a[64], b[64], ch[64];

      NE::cartOn();
      for (uint8_t i = 0; i < 64; i++) { a[i] = NE::read_prg_byte(0x8000 + i); b[i] = NE::read_prg_byte(0xC000 + i); ch[i] = NE::read_chr_byte(i); }
      if (allSame(a, 64) && allSame(b, 64) && (a[0] == 0xFF || a[0] == 0x00)) return oscr::E_SEM_CARTUCHO;

      nesRec = NE::crdbNESRecord{};
      NE::romDetail = &nesRec;
      NE::mmc6 = false;
      NE::flashfound = false;
      fromCRDB = false;
      nesRec.mapper = m;
      nesPrgBytes = nesChrBytes = nesRamBytes = 0;

      if (forSave)
      {
        if (!nesHasSave(m)) return oscr::E_SEM_SAVE;
        uint16_t ram = prgKb ? prgKb : 8;
        if (ram != 8 && !((m == 1 || m == 5) && (ram == 16 || ram == 32))) return oscr::E_ARGUMENTO;     // 16/32 KB só no MMC1 (SOROM/SXROM) e no MMC5
        nesRec.ram = log2u(ram / 4);                                  // 8 KB = 1, 16 KB = 2, 32 KB = 3 (ramSizes do núcleo)
        nesRec.prg = 0;
        NE::checkStatus();                                            // preenche ramsize; no MMC6 acha a RAM de 1 KB
        nesRamBytes = uint32_t(nesRec.ramsize) * 1024UL;
        snprintf(nesName, sizeof nesName, "mapper %u", unsigned(m));
        return 0;
      }

      uint16_t prg, chr;
      if (m == 0 && prgKb == 0)                                       // automático: NROM
      {
        prg = memcmp(a, b, 64) == 0 ? 16 : 32;
        chr = (allSame(ch, 64) && (ch[0] == 0xFF || ch[0] == 0x00)) ? 0 : 8;
        strlcpy(nesName, "NROM (mapper 0)", sizeof nesName);
      }
      else
      {
        prg = prgKb; chr = chrKb;
        uint16_t rc = nesCheckRom(m, prg, chr);
        if (rc) return rc;
        snprintf(nesName, sizeof nesName, "mapper %u", unsigned(m));
      }

      nesRec.prg = log2u(prg / 16);
      nesRec.chr = chr ? log2u(chr / 4) : 0;
      nesRec.ram = 0;
      NE::checkStatus();
      nesPrgBytes = uint32_t(prg) * 1024UL;
      nesChrBytes = uint32_t(chr) * 1024UL;

      uint8_t * h = nesRec.iNES;                                      // cabeçalho iNES sintético: tamanhos e mapper; espelhamento e bateria ficam 0
      h[0] = 'N'; h[1] = 'E'; h[2] = 'S'; h[3] = 0x1A;
      h[4] = uint8_t(prg / 16); h[5] = uint8_t(chr / 8);
      h[6] = uint8_t((m & 0x0F) << 4); h[7] = uint8_t(m & 0xF0);
      return 0;
    }

    /** Backend dos núcleos do OSCR: SNES, NES/Famicom, Mega Drive, Game Boy Advance e Game Boy/Color. */
    class CoreBackend : public oscr::Backend
    {
    public:
      bool power_switch() override { return kPowerSwitch; }
      bool cart_powered() override { return powerOn; }
      bool cart_power(bool on, uint16_t & err) override
      {
        if (on == powerOn) return true;
        if (on)
        {
          railUp();
        }
        else railDown();
        powerOn = on;
        return true;
      }
      void power_info(oscr::PowerInfo & p) override
      {
        p.on = powerOn;
        p.features = uint8_t((OSCR_POWER_SENSE ? 2 : 0) | (OSCR_POWER_DISCHARGE ? 4 : 0));
        p.sw = 0xFF;                                  // reservado: não há chave física (D123)
        p.rail = OSCR_POWER_SENSE ? (railLow() ? 0 : 1) : 0xFF;
      }

      uint8_t flags() override { return 8 | 16; }     // bit3: o firmware aceita WRITE_ROM (flash repro); bit4: programador de flash genérico (sistema 7, ERASE)
      uint16_t systems() override { return (1U << oscr::SYS_SNES) | (1U << oscr::SYS_NES) | (1U << oscr::SYS_FAMICOM) | (1U << oscr::SYS_MD) | (1U << oscr::SYS_GBA) | (1U << oscr::SYS_GB) | (1U << oscr::SYS_FLASH); }
      bool supports(uint8_t system) override { return system == oscr::SYS_SNES || isNes(system) || system == oscr::SYS_MD || system == oscr::SYS_GBA || system == oscr::SYS_GB || system == oscr::SYS_FLASH; }
      bool streams() override { return true; }

      // GBA: o campo `mapper` do protocolo é o tipo de save (numeração do OSCR); valores acima de 6 são recusados.
      // SNES: `prg_kb` é o tamanho da ROM em KB (0 = pelo cabeçalho).
      // NES/Famicom: mapper, PRG e CHR em KB (0 = NROM automático); nos saves, `prg_kb` é a RAM em KB (0 = 8).
      void set_options(uint16_t mapper, uint16_t prg, uint16_t chr) override { optMapper = mapper; optPrgKb = prg; optChrKb = chr; }

      void detect(uint8_t system, oscr::DetectInfo & out) override
      {
        if (!supports(system)) { out.status = 2; return; }

        if (system == oscr::SYS_FLASH)
        {
          // Programador genérico: as opções (chip, tamanho, tipo) vêm no próprio DETECT; o "nome" é o ID lido do chip.
          uint16_t chip = optMapper, prg = optPrgKb, chr = optChrKb;
          if (FlashProg::checkDetect(chip, prg, chr)) { out.status = 2; return; }
          uint8_t st = 1; uint32_t size = 0;
          out.name[0] = 0;
          if (chip == FlashProg::kMdCart)
          {
            // Flash do cartucho de Mega Drive: o nome é "CHIP FFDD" (fabricante e dispositivo). Status 0 = chip da tabela; 1 = ID desconhecido
            // (o nome traz "?" e o ID lido, para o PC mostrar). A sondagem escreve comandos de ID no cartucho (ROM de máscara os ignora).
            uint16_t rc = oscr::E_FLASH;
            bool ranMd = runCore([&] { rc = MdFlash::identify(out.name, size); MD::cartOff(); });
            out.status = (ranMd && rc == 0) ? 0 : 1;
            out.rom_size = size;
            out.save_size = 0; out.save_type = 0;
            return;
          }
          bool ran = runCore([&] { st = FlashProg::detect(chip, prg, chr, out.name, size); OSCR::Cores::SNES::cartOff(); });
          out.status = ran ? st : 1;
          out.rom_size = size;
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_GBA)
        {
          uint8_t st = 1;
          bool ran = runCore([&st] { st = gbaProbe(0); });
          if (!ran && st == 1) { out.status = 1; return; }
          out.status = st;
          if (st == 1) return;
          out.rom_size = OSCR::Cores::cartSize;
          out.save_size = 32768;                  // o tipo real (SRAM, Flash ou EEPROM) o usuário informa; o cabeçalho não diz
          out.save_type = 255;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        if (isNes(system))
        {
          uint16_t rc = oscr::E_SEM_CARTUCHO;
          bool ran = runCore([&rc] { rc = nesProbe(false, 0, 0, 0); NE::cartOff(); });   // o DETECT ignora as opções: NROM automático
          if (!ran || rc != 0) { out.status = rc == oscr::E_SEM_CARTUCHO || !ran ? 1 : 2; return; }
          out.status = 0;
          out.rom_size = 16UL + nesPrgBytes + nesChrBytes;
          out.save_size = 0;                                     // o PC informa mapper e RAM; o cartucho não diz
          out.save_type = 0;
          strlcpy(out.name, nesName, sizeof(out.name));
          return;
        }

        if (system == oscr::SYS_SNES)
        {
          uint8_t st = 1;
          uint16_t kb = 0;                                       // o DETECT ignora as opções
          runCore([&st, kb] { st = snesProbe(kb); });
          out.status = st;
          out.attempts = probeAttempts;
          if (st == 1) return;
          out.rom_size = uint32_t(OSCR::Cores::romSize) * 131072UL;
          out.save_size = uint32_t(OSCR::Cores::sramSize) * 128UL;
          out.save_type = out.save_size ? 1 : 0;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        if (system == oscr::SYS_GB)
        {
          uint8_t st = 1;
          runCore([&st] { st = gbProbe(); GB::cartOff(); });
          out.status = st;
          if (st == 1) return;
          out.rom_size = uint32_t(GB::romBanks) * 16384UL;
          out.save_size = gbSaveBytes();
          out.save_type = out.save_size ? 1 : 0;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        bool ok = runCore([] { MD::getCartInfo(); MD::cartOff(); });

        // O OSCR considera "sem cartucho" um tamanho zero ou absurdo (o maior jogo conhecido tem 10 MB).
        // Sem cabeçalho legível: se o /CART está baixo há cartucho (contato sujo ou mal encaixado): status 4 em vez de 1. Alto: como antes.
        if (!ok || OSCR::Cores::cartSize == 0 || OSCR::Cores::cartSize > 16777216UL) { out.status = mdCartPinLow() ? 4 : 1; return; }

        out.status = 0;
        out.rom_size = OSCR::Cores::cartSize;
        out.save_size = OSCR::Cores::saveType == 4 ? MD::eepSize : OSCR::Cores::sramSize;
        out.save_type = OSCR::Cores::saveType;
        strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
      }

      bool stream_read(uint8_t system, uint8_t kind, oscr::StreamSink & sink, uint16_t & err) override
      {
        if (!supports(system)) { err = oscr::E_SISTEMA; return false; }

        if (system == oscr::SYS_FLASH)                            // programador genérico: ler o chip inteiro (o conteúdo vai ao PC; "em branco" é conferido lá)
        {
          uint16_t chip = optMapper, prg = optPrgKb;
          if (kind != oscr::KIND_ROM) { err = oscr::E_COMANDO; return false; }
          if (FlashProg::check(chip, prg, optChrKb, 0)) { err = oscr::E_ARGUMENTO; return false; }
          countingSink.inner = &sink; countingSink.bytes = 0;
          activeSink = &countingSink;
          bool ok = runCore([chip, prg] { FlashProg::read(chip, prg); OSCR::Cores::SNES::cartOff(); });
          activeSink = nullptr;
          err = oscr::E_CARTUCHO_IO;
          return ok && countingSink.bytes > 0;
        }

        if (!prepare(system, kind == oscr::KIND_SAVE, err)) return false;

        uint8_t saveType = OSCR::Cores::saveType;
        if (isNes(system)) { if (kind == oscr::KIND_SAVE && nesRamBytes == 0) { err = oscr::E_SEM_SAVE; return false; } }
        else if (system == oscr::SYS_SNES) { if (kind == oscr::KIND_SAVE && OSCR::Cores::sramSize < 1) { err = oscr::E_SEM_SAVE; return false; } }
        else if (system == oscr::SYS_GB) { if (kind == oscr::KIND_SAVE && gbSaveBytes() == 0) { err = oscr::E_SEM_SAVE; return false; } }
        else if (kind == oscr::KIND_SAVE && saveType == 0) { err = oscr::E_SEM_SAVE; return false; }

        countingSink.inner = &sink; countingSink.bytes = 0;
        activeSink = &countingSink;
        bool ok = runCore([system, kind, saveType]
        {
          if (isNes(system))
          {
            NE::cartOn();
            if (kind == oscr::KIND_ROM)
            {
              OSCR::Storage::Shared::sharedFile.open("rom", O_WRONLY | O_CREAT | O_TRUNC);
              OSCR::Storage::Shared::sharedFile.write(nesRec.iNES, 16);       // o CRC32 do arquivo (no END) inclui o cabeçalho, como no firmware próprio
              NE::readPRG(true);
              NE::readCHR(true);
            }
            else
            {
              NE::readRAM();
            }
            NE::cartOff();
            return;
          }
          if (system == oscr::SYS_GBA)
          {
            if (kind == oscr::KIND_ROM) GBA::readROM(); else GBA::readSave();
            return;
          }
          if (system == oscr::SYS_SNES)
          {
            if (kind == oscr::KIND_ROM) SN::readROM(); else SN::readSRAM();
            SN::cartOff();
            return;
          }
          if (system == oscr::SYS_GB)
          {
            if (kind == oscr::KIND_ROM) GB::readROM(); else GB::readSave();
            GB::cartOff();
            return;
          }
          if (kind == oscr::KIND_ROM)
          {
            MD::readROM();
          }
          else if (saveType == 4)
          {
            MD::readEEP();
          }
          else
          {
            MD::cartOn(); MD::enableSram(1); MD::readSram(); MD::enableSram(0); MD::cartOff();
          }
        }, true);
        activeSink = nullptr;

        // Avisos do OSCR depois que o dado já saiu (checksum, base de dados) não anulam a leitura; sem nenhum byte, é falha.
        err = oscr::E_CARTUCHO_IO;
        return ok || (!fatalHit && countingSink.bytes > 0);
      }

      bool stream_write(uint8_t system, oscr::StreamSource & in, uint16_t & err) override
      {
        if (!supports(system)) { err = oscr::E_SISTEMA; return false; }
        if (!prepare(system, true, err)) return false;

        uint8_t saveType = OSCR::Cores::saveType;
        uint32_t expected = isNes(system) ? nesRamBytes
                          : system == oscr::SYS_GBA ? gbaSaveBytes(saveType)
                          : (system == oscr::SYS_GB ? gbSaveBytes()
                          : (system == oscr::SYS_SNES ? uint32_t(OSCR::Cores::sramSize) * 128UL : (saveType == 4 ? MD::eepSize : OSCR::Cores::sramSize)));

        if ((system != oscr::SYS_GB && system != oscr::SYS_SNES && !isNes(system) && saveType == 0) || expected == 0) { err = oscr::E_SEM_SAVE; return false; }
        if (in.size() != expected) { err = oscr::E_ARGUMENTO; return false; }

        countingSource.inner = &in; countingSource.bytes = 0;
        activeSource = &countingSource;
        OSCR::Storage::Shared::sharedFile.open("save", O_RDONLY);    // o "arquivo" é o que o PC manda
        bool ok = runCore([system, saveType]
        {
          if (isNes(system))
          {
            NE::cartOn();
            NE::writeRAM();               // a conferência do OSCR relê o arquivo (não existe no fluxo): o PC relê o save e compara
            NE::cartOff();
            return;
          }
          if (system == oscr::SYS_GBA)
          {
            GBA::writeSave();
            return;
          }
          if (system == oscr::SYS_SNES)
          {
            SN::writeSRAM(true);          // a verificação do OSCR relê o arquivo (não existe no fluxo): o PC relê o save e compara
            SN::cartOff();
            return;
          }
          if (system == oscr::SYS_GB)
          {
            GB::writeSave();
            GB::cartOff();
            return;
          }
          if (saveType == 4)
          {
            MD::writeEEP();
          }
          else
          {
            MD::cartOn(); MD::enableSram(1); MD::writeSram(); MD::enableSram(0); MD::cartOff();
          }
        }, true);
        activeSource = nullptr;

        // A verificação do OSCR relê o arquivo, que não existe no fluxo; vale ter consumido o arquivo inteiro sem erro fatal.
        err = oscr::E_CARTUCHO_IO;
        return ok || (!fatalHit && countingSource.bytes == expected);
      }

      // WRITE_ROM. Opções: `mapper` = chip (NES: NesFlash::kNesMaker, kA29040B; SNES: SnesFlash::kCfiLoRom, kCfiHiRom);
      // NES: `prg_kb` e `chr_kb` = tamanhos que o PC tirou do arquivo; SNES: `prg_kb` = capacidade do flash em KB.
      bool rom_prepare(uint8_t system, uint32_t size, uint16_t & err) override
      {
        uint8_t chip = uint8_t(optMapper); uint16_t prg = optPrgKb, chr = optChrKb;
        uint16_t rc;
        bool ran;
        romWriteSize = size;
        if (isNes(system))
        {
          rc = NesFlash::check(chip, prg, chr, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_CARTUCHO_IO;
          ran = runCore([&rc, chip, prg, chr] { NE::cartOn(); rc = NesFlash::prepare(chip, prg, chr); NE::cartOff(); });
        }
        else if (system == oscr::SYS_SNES)
        {
          uint16_t code = optMapper;                                    // SNES: o campo inteiro (disposição << 8 | fiação)
          rc = SnesFlash::check(code, prg, chr, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_CARTUCHO_IO;
          ran = runCore([&rc, code, prg, chr, size] { rc = SnesFlash::prepare(code, prg, chr, size); SN::cartOff(); });
        }
        else if (system == oscr::SYS_MD)
        {
          rc = MdFlash::check(chip, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_CARTUCHO_IO;
          ran = runCore([&rc, size] { rc = MdFlash::prepare(size); MD::cartOff(); });
        }
        else if (system == oscr::SYS_GBA)
        {
          uint16_t code = optMapper;                                    // GBA: (bloco << 8) | 1; o bloco só vale no 369-in-1
          rc = GbaFlash::check(code, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_FLASH;                                           // o `idFlashrom` do OSCR faz fatalError se não reconhece o chip
          ran = runCore([&rc, code, size] { rc = GbaFlash::prepare(code, size); GBA::cartOff(); });
        }
        else if (system == oscr::SYS_GB)
        {
          rc = GbFlash::check(chip, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_FLASH;
          ran = runCore([&rc, chip, size] { rc = GbFlash::prepare(chip, size); GB::cartOff(); });
          GB::audioWE = 0;                                              // o pino de áudio como WE só vale durante a gravação
        }
        else if (system == oscr::SYS_FLASH)
        {
          uint16_t code = optMapper;
          rc = size ? FlashProg::check(code, prg, chr, size) : oscr::E_ARGUMENTO;
          if (rc) { err = rc; return false; }
          rc = oscr::E_FLASH;
          ran = runCore([&rc, code, prg, chr, size] { rc = FlashProg::prepare(code, prg, chr, size); OSCR::Cores::SNES::cartOff(); });
        }
        else { err = oscr::E_COMANDO; return false; }
        if (rc != 0 || !ran) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        return true;
      }

      bool stream_write_rom(uint8_t system, oscr::StreamSource & in, uint16_t & err) override
      {
        uint8_t chip = uint8_t(optMapper); uint16_t prg = optPrgKb, chr = optChrKb;
        uint16_t rc = oscr::E_CARTUCHO_IO;
        bool ran;
        if (isNes(system)) ran = runCore([&rc, &in, chip, prg, chr] { NE::cartOn(); rc = NesFlash::program(chip, prg, chr, in); NE::cartOff(); });
        else if (system == oscr::SYS_SNES)
        {
          uint16_t code = optMapper; uint32_t n = romWriteSize;
          bool generic = SnesFlash::isGeneric(code);
          if (generic)                                                  // P0/P1: as funções do OSCR leem o "arquivo" (sharedFile); ligá-lo ao fluxo, como no WRITE_SAVE
          {
            countingSource.inner = &in; countingSource.bytes = 0;
            activeSource = &countingSource;
            OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
          }
          ran = runCore([&rc, &in, code, prg, chr, n] { rc = SnesFlash::program(code, prg, chr, n, in); SN::cartOff(); });
          if (generic)
          {
            activeSource = nullptr;
            if (rc == 0 && countingSource.bytes != n) rc = oscr::E_CARTUCHO_IO;     // o OSCR não avisa se o arquivo acabou antes
          }
        }
        else if (system == oscr::SYS_MD)
        {
          // As funções do OSCR leem o "arquivo" (sharedFile): ligá-lo ao fluxo, como no WRITE_SAVE.
          countingSource.inner = &in; countingSource.bytes = 0;
          activeSource = &countingSource;
          OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
          ran = runCore([&rc] { rc = MdFlash::program(); MD::cartOff(); });
          activeSource = nullptr;
          if (rc == 0 && countingSource.bytes != romWriteSize) rc = oscr::E_CARTUCHO_IO;       // o OSCR não avisa se o arquivo acabou antes
        }
        else if (system == oscr::SYS_GBA)
        {
          // As funções do OSCR leem o "arquivo" (sharedFile): ligá-lo ao fluxo, como no WRITE_SAVE.
          uint16_t code = optMapper; uint32_t n = romWriteSize;
          countingSource.inner = &in; countingSource.bytes = 0;
          activeSource = &countingSource;
          OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
          ran = runCore([&rc, code, n] { rc = GbaFlash::program(code, n); GBA::cartOff(); });
          activeSource = nullptr;
          if (rc == 0 && countingSource.bytes != n) rc = oscr::E_CARTUCHO_IO;
        }
        else if (system == oscr::SYS_GB)
        {
          uint32_t n = romWriteSize;
          ran = runCore([&rc, &in, chip, n] { rc = GbFlash::program(chip, n, in); GB::cartOff(); });
          GB::audioWE = 0;
        }
        else if (system == oscr::SYS_FLASH)
        {
          uint16_t code = optMapper; uint32_t n = romWriteSize;
          countingSource.inner = &in; countingSource.bytes = 0;
          activeSource = &countingSource;
          OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
          ran = runCore([&rc, &in, code, prg, chr, n] { rc = FlashProg::program(code, prg, chr, n, in); OSCR::Cores::SNES::cartOff(); });
          activeSource = nullptr;
          if (rc == 0 && countingSource.bytes != n) rc = oscr::E_CARTUCHO_IO;       // todas as rotinas do OSCR leem o "arquivo"; sem consumir tudo, a gravação ficou incompleta
        }
        else { err = oscr::E_COMANDO; return false; }
        if (rc != 0 || !ran) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        return true;
      }

      // ERASE (programador genérico): apaga o chip inteiro. 8 bits: o tipo é obrigatório (identifica o chip antes e escolhe a rotina de apagar).
      bool erase(uint8_t system, uint16_t & err) override
      {
        if (system != oscr::SYS_FLASH) { err = oscr::E_COMANDO; return false; }
        uint16_t code = optMapper, prg = optPrgKb, chr = optChrKb;
        uint16_t rc = FlashProg::check(code, prg, chr, 0);
        bool needsType = (code & 0xFF) == FlashProg::k8Adapter || (code & 0xFF) == FlashProg::k8Plcc32;
        if (rc || (needsType && ((chr & 0xF) < 1 || (chr & 0xF) > 8)) || (code & 0xFF) == FlashProg::kEprom) { err = oscr::E_ARGUMENTO; return false; }
        rc = oscr::E_FLASH;
        bool ran = runCore([&rc, code, prg, chr] { rc = FlashProg::prepare(code, prg, chr, 0); OSCR::Cores::SNES::cartOff(); });
        if (rc != 0 || !ran) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        return true;
      }

      // Caminhos que o modo fluxo não usa.
      bool open_read(uint8_t, uint8_t, uint32_t &, uint16_t & err) override { err = oscr::E_COMANDO; return false; }
      bool read(uint8_t, uint8_t, uint32_t, uint8_t *, uint16_t) override { return false; }
      bool write_begin(uint8_t, uint32_t, uint16_t & err) override { err = oscr::E_COMANDO; return false; }
      bool write_block(uint32_t, uint8_t const *, uint16_t) override { return false; }
      bool write_commit() override { return false; }

    private:
      uint16_t optMapper = 0, optPrgKb = 0, optChrKb = 0;
      uint32_t romWriteSize = 0;      // tamanho do arquivo do último WRITE_ROM (rom_prepare -> stream_write_rom)

      /** Lê o cabeçalho do cartucho (preenche cartSize, saveType, sramSize...) antes de ler ou gravar. */
      bool prepare(uint8_t system, bool forSave, uint16_t & err)
      {
        if (system == oscr::SYS_GBA)
        {
          if (forSave && optMapper > 6) { err = oscr::E_ARGUMENTO; return false; }
          uint8_t st = 1;
          runCore([&st, this] { st = gbaProbe(uint8_t(optMapper)); });
          if (st == 1) { err = oscr::E_SEM_CARTUCHO; return false; }     // 4 (checksum do cabeçalho errado) segue: o PC decide
          if (!forSave && optPrgKb) OSCR::Cores::cartSize = uint32_t(optPrgKb) * 1024UL;   // tamanho informado (conferência depois de gravar o flash: a detecção por espelho vê o flash inteiro)
          return true;
        }
        if (system == oscr::SYS_SNES)
        {
          uint8_t st = 1;
          uint16_t kb = forSave ? uint16_t(0) : optPrgKb;
          runCore([&st, kb] { st = snesProbe(kb); });
          if (st == 1) { err = oscr::E_SEM_CARTUCHO; return false; }
          if (st != 0) { err = oscr::E_CARTUCHO_IO; return false; }
          return true;
        }
        if (isNes(system))
        {
          uint16_t rc = oscr::E_SEM_CARTUCHO;
          uint16_t m = optMapper, p = optPrgKb, c = optChrKb;
          bool ran = runCore([&rc, forSave, m, p, c] { rc = nesProbe(forSave, m, p, c); NE::cartOff(); });
          if (!ran && rc == oscr::E_SEM_CARTUCHO) { err = oscr::E_CARTUCHO_IO; return false; }
          if (rc != 0) { err = rc; return false; }
          return true;
        }
        if (system == oscr::SYS_GB)
        {
          uint8_t st = 1;
          runCore([&st] { st = gbProbe(); GB::cartOff(); });
          if (st == 1) { err = oscr::E_SEM_CARTUCHO; return false; }
          if (st != 0) { err = oscr::E_CARTUCHO_IO; return false; }      // 4: checksum do cabeçalho errado (limpar os contatos e tentar de novo)
          return true;
        }
        oscr::DetectInfo d;
        detect(system, d);
        if (d.status != 0) { err = oscr::E_SEM_CARTUCHO; return false; }
        return true;
      }
    };

    CoreBackend backend;
    oscr::Session * session = nullptr;
  }

  oscr::StreamSink * sink() { return activeSink; }
  oscr::StreamSource * source() { return activeSource; }

  void noteError() { errorFlag = true; }

  void noteAbort() { abortHit = true; }

  [[ noreturn ]] void fatal()
  {
    errorFlag = true;
    if (armed) longjmp(escape, 1);

    // Erro fora de um comando (por exemplo no setup): nada a fazer além de parar com a serial muda.
    for (;;) {}
  }

  void setup()
  {
    if (OSCR_POWER_SENSE) { DDRB &= ~_BV(PB0); PORTB &= ~_BV(PB0); }        // sensor do rail no D53: entrada sem pull-up
    if (kPowerSwitch) { cartPower(false); powerOn = false; }                  // placa com a chave de 5V em software: começa desligado, o host liga (D115)
    else cartPower(true);                     // sem isso o cartucho fica sem 5V; o OSCR original não tinha chave
    delay(50);                                // o 5V dos slots, o Si5351 e o PIC sobem antes do primeiro comando
    ClockedSerial.begin(OSCR_DUMPER_BAUD);
    ClockedSerial.mute = true;                // a UI de texto do OSCR não pode escrever no meio dos quadros

    static oscr::Session s(oscr::Io{nullptr, ioRead, ioWrite, ioNow}, backend, rxBuf, sizeof rxBuf, txBuf, sizeof txBuf);
    session = &s;
  }

  void loop()
  {
    if (session != nullptr) session->poll();
  }
}

#endif /* OSCR_DUMPER */
