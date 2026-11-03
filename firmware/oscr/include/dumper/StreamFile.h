// SPDX-License-Identifier: GPL-3.0-or-later
// Fork oscr_minimal: no lugar do cartão SD, o "arquivo" do OSCR é um fluxo do protocolo serial.
//  - aberto para escrita (O_CREAT/O_WRITE/O_RDWR): cada `write` vai ao PC em quadros DATA (src/dumper/oscr_session.cpp);
//  - aberto só para leitura: cada `read` pede ao PC o próximo trecho do arquivo (WRITE_SAVE).
// Sem SD não há `seek` de verdade: só o que os núcleos fazem na prática está coberto (ver docs/fork-oscr.md).
#pragma once
#include "syslibinc.h"

namespace OSCR::Storage
{
  class StreamFile
  {
  public:
    bool open(char const * name, oflag_t oflag);
    bool open(uint32_t index, oflag_t oflag);
    bool close();
    bool isOpen() const { return opened; }
    int read();
    int read(void * buf, size_t count);
    int peek();
    size_t readBytesUntil(char terminator, uint8_t * buf, size_t count);
    size_t readBytesUntil(char terminator, char * buf, size_t count) { return readBytesUntil(terminator, (uint8_t *)buf, count); }
    size_t write(uint8_t byte);
    size_t write(uint8_t const * buf, size_t count);
    bool getWriteError() const { return writeError; }
    void sync() {}
    uint64_t fileSize() const;
    uint64_t available64() const;
    uint64_t curPosition() const { return pos; }
    bool seekSet(uint64_t p);
    bool seekEnd(int64_t offset = 0);
    void rewind() { seekSet(0); }
    bool rename(char const *) { return true; }
    bool remove() { return true; }
    bool isFile() const { return true; }
    bool isDir() const { return false; }
    bool getName(char * name, size_t len) { if (len) name[0] = 0; return true; }
    bool find(uint8_t const *) { return false; }
    bool find(char const *) { return false; }

  protected:
    bool opened = false;
    bool writing = false;
    bool writeError = false;
    uint64_t pos = 0;       // posição lógica (bytes escritos ou lidos)
    uint8_t peeked = 0;
    bool hasPeek = false;
  };

  // Substitui o SdFs: não há sistema de arquivos.
  class StreamSd
  {
  public:
    bool begin() { return true; }
    bool exists(char const *) { return false; }
    bool mkdir(char const *, bool = true) { return true; }
    bool chdir(char const * = nullptr) { return true; }
  };
}
