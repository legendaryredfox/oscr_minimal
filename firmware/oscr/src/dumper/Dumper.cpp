// SPDX-License-Identifier: GPL-3.0-or-later
// Fork oscr_minimal: laço de comandos do protocolo serial (docs/protocolo.md) ligado aos núcleos do OSCR.
// Estado: Mega Drive e Game Boy Advance (DETECT, DUMP_ROM, READ_SAVE e WRITE_SAVE). SNES, NES e GB/GBC ainda não (docs/fork-oscr.md).
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
# include "dumper/Dumper.h"

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
     * Executa uma função de núcleo com a saída ligada ao fluxo. Erros fatais dos núcleos (UI::fatalError) voltam aqui por longjmp.
     * Devolve false se o núcleo falhou.
     */
    bool fatalHit = false;

    template <typename Fn>
    bool runCore(Fn fn, bool softErrors = false)
    {
      errorFlag = false;
      fatalHit = false;
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

    /** Backend dos núcleos do OSCR: Mega Drive, Game Boy Advance e Game Boy/Color. */
    class CoreBackend : public oscr::Backend
    {
    public:
      uint8_t flags() override { return 0; }
      uint16_t systems() override { return (1U << oscr::SYS_MD) | (1U << oscr::SYS_GBA) | (1U << oscr::SYS_GB); }
      bool supports(uint8_t system) override { return system == oscr::SYS_MD || system == oscr::SYS_GBA || system == oscr::SYS_GB; }
      bool streams() override { return true; }

      // GBA: o campo `mapper` do protocolo é o tipo de save (numeração do OSCR); valores acima de 6 são recusados.
      void set_options(uint16_t mapper, uint16_t prg, uint16_t chr) override { optMapper = mapper; (void)prg; (void)chr; }

      void detect(uint8_t system, oscr::DetectInfo & out) override
      {
        if (!supports(system)) { out.status = 2; return; }

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
        if (!ok || OSCR::Cores::cartSize == 0 || OSCR::Cores::cartSize > 16777216UL) { out.status = 1; return; }

        out.status = 0;
        out.rom_size = OSCR::Cores::cartSize;
        out.save_size = OSCR::Cores::saveType == 4 ? MD::eepSize : OSCR::Cores::sramSize;
        out.save_type = OSCR::Cores::saveType;
        strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
      }

      bool stream_read(uint8_t system, uint8_t kind, oscr::StreamSink & sink, uint16_t & err) override
      {
        if (!supports(system)) { err = oscr::E_SISTEMA; return false; }
        if (!prepare(system, kind == oscr::KIND_SAVE, err)) return false;

        uint8_t saveType = OSCR::Cores::saveType;
        if (system == oscr::SYS_GB) { if (kind == oscr::KIND_SAVE && gbSaveBytes() == 0) { err = oscr::E_SEM_SAVE; return false; } }
        else if (kind == oscr::KIND_SAVE && saveType == 0) { err = oscr::E_SEM_SAVE; return false; }

        countingSink.inner = &sink; countingSink.bytes = 0;
        activeSink = &countingSink;
        bool ok = runCore([system, kind, saveType]
        {
          if (system == oscr::SYS_GBA)
          {
            if (kind == oscr::KIND_ROM) GBA::readROM(); else GBA::readSave();
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
        uint32_t expected = system == oscr::SYS_GBA ? gbaSaveBytes(saveType) : (system == oscr::SYS_GB ? gbSaveBytes() : (saveType == 4 ? MD::eepSize : OSCR::Cores::sramSize));

        if ((system != oscr::SYS_GB && saveType == 0) || expected == 0) { err = oscr::E_SEM_SAVE; return false; }
        if (in.size() != expected) { err = oscr::E_ARGUMENTO; return false; }

        countingSource.inner = &in; countingSource.bytes = 0;
        activeSource = &countingSource;
        OSCR::Storage::Shared::sharedFile.open("save", O_RDONLY);    // o "arquivo" é o que o PC manda
        bool ok = runCore([system, saveType]
        {
          if (system == oscr::SYS_GBA)
          {
            GBA::writeSave();
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

      // Caminhos que o modo fluxo não usa.
      bool open_read(uint8_t, uint8_t, uint32_t &, uint16_t & err) override { err = oscr::E_COMANDO; return false; }
      bool read(uint8_t, uint8_t, uint32_t, uint8_t *, uint16_t) override { return false; }
      bool write_begin(uint8_t, uint32_t, uint16_t & err) override { err = oscr::E_COMANDO; return false; }
      bool write_block(uint32_t, uint8_t const *, uint16_t) override { return false; }
      bool write_commit() override { return false; }

    private:
      uint16_t optMapper = 0;

      /** Lê o cabeçalho do cartucho (preenche cartSize, saveType, sramSize...) antes de ler ou gravar. */
      bool prepare(uint8_t system, bool forSave, uint16_t & err)
      {
        if (system == oscr::SYS_GBA)
        {
          if (forSave && optMapper > 6) { err = oscr::E_ARGUMENTO; return false; }
          uint8_t st = 1;
          runCore([&st, this] { st = gbaProbe(uint8_t(optMapper)); });
          if (st == 1) { err = oscr::E_SEM_CARTUCHO; return false; }     // 4 (checksum do cabeçalho errado) segue: o PC decide
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

  [[ noreturn ]] void fatal()
  {
    errorFlag = true;
    if (armed) longjmp(escape, 1);

    // Erro fora de um comando (por exemplo no setup): nada a fazer além de parar com a serial muda.
    for (;;) {}
  }

  void setup()
  {
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
