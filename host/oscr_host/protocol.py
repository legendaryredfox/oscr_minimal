# SPDX-License-Identifier: GPL-3.0-or-later
"""Quadros, tipos e (de)serialização do protocolo v1. Sem dependência de serial."""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

PROTO_VERSION = 1
MAGIC = b"\xA5\x5A"
MAX_PAYLOAD = 1024
DEFAULT_BLOCK = 512
MIN_BLOCK = 64                   # abaixo disso cada quadro leva um ACK por poucos bytes: 1 byte por bloco passa de 90 s para 128 KB (D199)
MAX_BLOCK = 516                  # OSCR_MAX_PAYLOAD (520) menos o offset de 4 bytes
HEADER_LEN = 6
CRC_LEN = 4

# host -> dispositivo
T_INFO, T_DETECT, T_DUMP_ROM, T_READ_SAVE, T_WRITE_SAVE = 0x01, 0x02, 0x03, 0x04, 0x05
T_ACK, T_NAK, T_ABORT, T_H_DATA, T_H_END = 0x06, 0x07, 0x08, 0x09, 0x0A
T_ERASE = 0x0C                         # programador de flash genérico (sistema 7): apaga o chip (docs/referencia/protocolo.md)
T_SELFTEST = 0x0E                       # autoteste da placa sem cartucho (P-12, docs/referencia/protocolo.md)
T_BOARD = 0x0F                          # perfil da placa: consulta ou grava na EEPROM do firmware (D162, docs/referencia/protocolo.md)
T_CLOCK = 0x10                          # relógio do Si5351: consulta, fator de correção (ppb) na EEPROM, saídas de teste (F-3, docs/referencia/protocolo.md)
T_VOLT = 0x0D                          # tensão dos slots: consulta ou escolhe 3,3 V/5 V (docs/referencia/protocolo.md, D138)
T_WRITE_ROM = 0x0B                     # igual ao WRITE_SAVE, mas grava a ROM em cartucho de flash (docs/referencia/protocolo.md)
# dispositivo -> host
T_INFO_RESP, T_DETECT_RESP, T_BEGIN, T_DATA, T_END = 0x81, 0x82, 0x83, 0x84, 0x85
T_D_ACK, T_ERRO, T_PROGRESSO = 0x86, 0x87, 0x88
BAUDS = (1_000_000, 500_000, 115_200)           # ordem em que o host tenta conectar (H-3); o firmware abre um só, escolhido na compilação (OSCR_DUMPER_BAUD)
STAGE_NONE, STAGE_ERASE, STAGE_WRITE, STAGE_READ, STAGE_SELFTEST = 0, 1, 2, 3, 4   # etapa do PROGRESSO (F-1)
STAGE_NAMES = {STAGE_ERASE: "erasing", STAGE_WRITE: "writing", STAGE_READ: "reading", STAGE_SELFTEST: "selftest"}
T_VOLT_RESP = 0x89
T_SELFTEST_RESP = 0x8A
T_BOARD_RESP = 0x8B
T_CLOCK_RESP = 0x8C
CLOCK_STATUS, CLOCK_SET, CLOCK_TEST_ON, CLOCK_TEST_OFF = 0, 1, 2, 3     # ação do CLOCK
CLOCK_MAX_PPB = 1_000_000               # limite de segurança do projeto (0,1 %); o firmware recusa acima
# Saídas de teste do CLOCK (as mesmas do `clkcal` do OSCR) e onde medir com o frequencímetro (wiki do OSCR, P-03). Todas saem do mesmo cristal: medir uma basta.
CLOCK_TARGETS = (
    {"output": "CLK0", "hz": 4_000_000, "where": "SNES pin 1 (EXT)"},
    {"output": "CLK2", "hz": 3_072_000, "where": "SNES pin 56 (CIC)"},
    {"output": "CLK1", "hz": 1_000_000, "where": "SNES pin 57 (CPU)"},
)
BOARD_STATUS, BOARD_SET = 0, 1                  # ação do BOARD
BOARD_VOLT_SELECT = 1                           # bit 0 do perfil: a placa tem o seletor de tensão 3,3 V/5 V (D138)
ST_GND, ST_PAIR, ST_NO_PULLUP, ST_NO_CLOCKGEN = 1, 2, 3, 4   # tipos de achado do SELFTEST
VOLT_STATUS, VOLT_3V3, VOLT_5V = 0, 1, 2       # ação do VOLT (seletor 3,3 V/5 V, D138)

KIND_ROM, KIND_SAVE = 1, 2

# Tipo de ROM do SNES forçado pelo PC (F-2, D164): vai no terceiro campo opcional (`chr_kb`), que o SNES não usa. 0 = pelo cabeçalho.
SNES_TYPES = {"lorom": 1, "hirom": 2, "sa1": 3, "exhirom": 4}
# Acessórios do SNES (F-10, D178): vão no mesmo 3º campo, a partir de 0x8000 (firmware/oscr/include/dumper/SnesAcc.h). Sufami Turbo: só ROM; GPC: só save de 512 KB.
SNES_ACCESSORIES = {"sufami-a": 0x8001, "sufami-b": 0x8002, "gpc": 0x8003,
                    "bsx-pack": 0x8004, "bsx-sram": 0x8005, "sfm-flash": 0x8006, "sfm-map": 0x8007,        # F-11 (D187): Satellaview BS-X e SF Memory Cassette
                    **{f"sfm-game-{n}": 0x8010 + n for n in range(7)}}
GPC_BYTES = 0x80000
SNES_SAVE_ACCESSORIES = {"gpc": GPC_BYTES, "bsx-sram": 0x8000}      # acessórios que são RAM (save-read e save-write) e o tamanho do arquivo; os outros são só ROM (dump)
SNES_ACC_EXT = {"sufami-a": ".st", "sufami-b": ".st", "bsx-pack": ".bs", "sfm-flash": ".bin", "sfm-map": ".map"}


def snes_acc_ext(name: str) -> str:
    """Extensão do arquivo de um acessório de ROM do SNES (os jogos do SFM saem como .sfc)."""
    return SNES_ACC_EXT.get(name, ".sfc")

SYSTEMS = {  # nome -> (id, extensão)
    "snes": (1, ".sfc"), "nes": (2, ".nes"), "famicom": (3, ".nes"),
    "md": (4, ".md"), "gba": (5, ".gba"), "gb": (6, ".gb"), "flash": (7, ".bin"), "sms": (8, ".sms"), "gg": (9, ".gg"), "sg1000": (10, ".sg"), "n64": (11, ".z64"), "coleco": (12, ".col"), "ngp": (13, ".ngp"), "vectrex": (14, ".vec"), "a2600": (15, ".a26"), "a5200": (16, ".a52"), "a7800": (17, ".a78"), "a8bit": (18, ".rom"), "lynx": (19, ".lnx"), "jaguar": (20, ".jag"), "arcadia": (21, ".bin"), "rca2": (22, ".bin"), "pyuuta": (23, ".bin"), "supervision": (24, ".sv"), "mock": (255, ".bin"),
}
SYSTEM_BY_ID = {v[0]: k for k, v in SYSTEMS.items()}


def system_name(i: int) -> str:
    return SYSTEM_BY_ID.get(i, str(i))

ERRORS = {
    1: "comando desconhecido ou não suportado", 2: "sistema desconhecido ou não suportado",
    3: "nenhum cartucho detectado", 4: "argumento inválido", 5: "reenvios excedidos",
    6: "CRC32 do arquivo não confere", 7: "erro de leitura/gravação no cartucho",
    8: "dispositivo ocupado", 9: "abortado", 10: "cartucho não tem save",
    11: "chip de flash não reconhecido",
}

# o que fazer para cada erro (a GUI tem os mesmos textos traduzidos em I18n.kt)
ERROR_HINTS = {
    1: "atualize o firmware e o programa para a mesma versão",
    2: "o chip, o mapper ou o sistema deste cartucho ainda não é lido (veja docs/referencia/uso.md)",
    3: "encaixe o cartucho até o fim, limpe os contatos e confira o sistema escolhido",
    4: "confira mapper, PRG, CHR, RAM e o tamanho do arquivo (docs/referencia/protocolo.md)",
    5: "troque o cabo, evite hubs USB ou use --baud 115200",
    6: "refaça a leitura; se repetir, limpe os contatos e troque o cabo",
    7: "confira a bateria e os contatos; numa gravação o save pode ter ficado incompleto: tente de novo e use o backup",
    8: "espere o fim da operação anterior",
    9: "operação cancelada",
    10: "este cartucho não tem save, ou o mapper/tipo informado não tem save",
    11: "o cartucho não é uma flash do tipo escolhido (ou está sujo/mal encaixado): confira o chip, os contatos e o encaixe; nada foi gravado",
}

UNKNOWN_SIZE = 0xFFFFFFFF            # BEGIN de núcleos em modo fluxo: o tamanho real vem no END
MAX_STREAM_BYTES = 256 << 20         # maior leitura aceita (GBA 369-in-1: 256 MB, D174; as outras vão até 64 MB); acima disso o BEGIN é tratado como defeito


class ProtocolError(Exception):
    pass


class DeviceError(Exception):
    """Dispositivo respondeu ERRO."""

    def __init__(self, code: int, text: str = ""):
        self.code, self.text = code, text
        hint = ERROR_HINTS.get(code)
        super().__init__(f"erro 0x{code:04X}: {ERRORS.get(code, 'desconhecido')}" + (f" ({text})" if text else "") + (f". Dica: {hint}" if hint else ""))


def crc32(data: bytes, start: int = 0) -> int:
    return zlib.crc32(data, start) & 0xFFFFFFFF


@dataclass
class Frame:
    type: int
    seq: int
    payload: bytes = b""


def encode_frame(type_: int, seq: int, payload: bytes = b"") -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise ProtocolError(f"payload de {len(payload)} bytes (máx. {MAX_PAYLOAD})")
    body = struct.pack("<BBH", type_, seq & 0xFF, len(payload)) + payload
    return MAGIC + body + struct.pack("<I", crc32(body))


class FrameDecoder:
    """Decodificador em fluxo: alimente com bytes, receba quadros válidos.

    Quadros com CRC ruim ou len inválido são descartados; o decodificador
    ressincroniza na próxima magia. `bad_frames` conta os descartes.
    """

    def __init__(self) -> None:
        self._buf = bytearray()
        self.bad_frames = 0

    def feed(self, data: bytes) -> list[Frame]:
        self._buf += data
        out: list[Frame] = []
        while True:
            i = self._buf.find(MAGIC)
            if i < 0:
                # mantém o último byte (pode ser metade da magia)
                if self._buf and self._buf[-1] == MAGIC[0]:
                    del self._buf[:-1]
                else:
                    self._buf.clear()
                break
            if i > 0:
                del self._buf[:i]
            if len(self._buf) < HEADER_LEN:
                break
            type_, seq, length = struct.unpack_from("<BBH", self._buf, 2)
            if length > MAX_PAYLOAD:
                self.bad_frames += 1
                del self._buf[:2]
                continue
            total = HEADER_LEN + length + CRC_LEN
            if len(self._buf) < total:
                break
            body = bytes(self._buf[2:HEADER_LEN + length])
            (got,) = struct.unpack_from("<I", self._buf, HEADER_LEN + length)
            if got != crc32(body):
                self.bad_frames += 1
                del self._buf[:2]
                continue
            out.append(Frame(type_, seq, bytes(self._buf[HEADER_LEN:HEADER_LEN + length])))
            del self._buf[:total]
        return out


# ---------------------------------------------------------------- builders / parsers
def build_info() -> bytes:
    return b""


def build_detect(system: int, chip: int = 0, prg_kb: int = 0, chr_kb: int = 0) -> bytes:
    base = struct.pack("<B", system)
    if chip or prg_kb or chr_kb:        # programador de flash genérico: as opções vão no próprio DETECT
        base += struct.pack("<HHH", chip, prg_kb, chr_kb)
    return base


def build_erase(system: int, chip: int, prg_kb: int, chr_kb: int) -> bytes:
    """ERASE (0x0C): sistema e as três opções do programador de flash genérico (docs/referencia/protocolo.md)."""
    return struct.pack("<BHHH", system, chip, prg_kb, chr_kb)


def build_dump(system: int, block: int = 0, mapper: int = 0, prg_kb: int = 0, chr_kb: int = 0) -> bytes:
    base = struct.pack("<BH", system, block)
    if mapper or prg_kb or chr_kb:      # opções do NES/Famicom (docs/referencia/protocolo.md)
        base += struct.pack("<HHH", mapper, prg_kb, chr_kb)
    return base


def build_write_save(system: int, size: int, block: int = 0, mapper: int = 0, ram_kb: int = 0, snes_type: int = 0) -> bytes:
    base = struct.pack("<BIH", system, size, block)
    if mapper or ram_kb or snes_type:   # NES/Famicom: mapper (1, 4, 5, 69, 118, 155, 19, 80 e 82 têm PRG-RAM com bateria; 16 e 159, EEPROM; D184) e RAM em KB (16/32 só nos mappers 1 e 5); SNES: tipo forçado no 3º campo (F-2)
        base += struct.pack("<HHH", mapper, ram_kb, snes_type)
    return base


def build_write_rom(system: int, size: int, block: int = 0, chip: int = 0, prg_kb: int = 0, chr_kb: int = 0) -> bytes:
    """WRITE_ROM: como o WRITE_SAVE, mas as três opções são sempre enviadas: chip, PRG e CHR em KB (docs/referencia/protocolo.md)."""
    return struct.pack("<BIHHHH", system, size, block, chip, prg_kb, chr_kb)


def build_offset(offset: int) -> bytes:  # ACK / NAK
    return struct.pack("<I", offset)


def build_data(offset: int, data: bytes) -> bytes:
    return struct.pack("<I", offset) + data


def build_end(total: int, crc: int) -> bytes:
    return struct.pack("<II", total, crc)


def parse_info_resp(p: bytes) -> dict:
    if len(p) < 7:
        raise ProtocolError("INFO_RESP curto")
    ver, ma, mi, pa, flags, systems = struct.unpack_from("<BBBBBH", p)
    max_payload = struct.unpack_from("<H", p, 7)[0] if len(p) >= 9 else MAX_PAYLOAD
    if len(p) >= 11:
        systems |= struct.unpack_from("<H", p, 9)[0] << 16   # ids 16 a 31 (D208); firmware antigo não manda
    return {"proto": ver, "firmware": f"{ma}.{mi}.{pa}", "flags": flags, "max_payload": max_payload,
            "mock": bool(flags & 1), "si5351": bool(flags & 2), "pic": bool(flags & 4), "write_rom": bool(flags & 8), "flash_prog": bool(flags & 16), "voltage_select": bool(flags & 32), "selftest": bool(flags & 64), "board_profile": bool(flags & 128),
            "systems": [n for n, (i, _) in SYSTEMS.items() if i < 32 and systems & (1 << i)],
            "system_ids": [i for i in range(32) if systems & (1 << i)]}


def parse_board_resp(p: bytes) -> dict:
    """BOARD_RESP (D162): `stored` = há perfil guardado na EEPROM do firmware; `voltage_select` = o perfil (ou, sem perfil, o padrão da compilação) tem o seletor."""
    if len(p) < 2:
        raise ProtocolError("BOARD_RESP curto")
    return {"stored": bool(p[0]), "voltage_select": bool(p[1] & BOARD_VOLT_SELECT)}


def build_clock(action: int, ppb: int = 0) -> bytes:
    """CLOCK: `u8 ação` e, no SET, `i32 fator` em ppb (positivo = a saída roda alta, ver a biblioteca Si5351)."""
    if action == CLOCK_SET:
        if abs(ppb) > CLOCK_MAX_PPB:
            raise ValueError(f"fator fora de ±{CLOCK_MAX_PPB} ppb")
        return struct.pack("<Bi", action, ppb)
    return bytes([action])


def parse_clock_resp(p: bytes) -> dict:
    """CLOCK_RESP: `present` = o Si5351 respondeu; `stored` = há fator na EEPROM; `ppb` = fator em vigor; `test` = saídas de teste ligadas."""
    if len(p) < 7:
        raise ProtocolError("CLOCK_RESP curto")
    return {"present": bool(p[0]), "stored": bool(p[1]), "ppb": struct.unpack_from("<i", p, 2)[0], "test": bool(p[6])}


def clock_factor_from_measure(measured_hz: float, target_hz: float, current_ppb: int = 0) -> int:
    """Fator (ppb) que corrige uma saída medida em `measured_hz` quando o alvo é `target_hz`, com `current_ppb` já em vigor durante a medição.
    A biblioteca trata a referência como ref*(1+c/1e9): medida/alvo = (1+e)/(1+c0/1e9), então c = ((medida/alvo)*(1+c0/1e9) - 1)*1e9."""
    if measured_hz <= 0 or target_hz <= 0:
        raise ValueError("frequências devem ser positivas")
    return round(((measured_hz / target_hz) * (1 + current_ppb / 1e9) - 1) * 1e9)


def parse_volt_resp(p: bytes) -> dict:
    """VOLT_RESP: seletor de tensão dos slots (D138). `voltage`: "3v3", "5v" ou "5v-fixed" (placa sem seletor). `chosen`: o usuário escolheu 3,3 V
    (a placa sobe em 3,3 V sem ninguém ter escolhido: só a escolha explícita exige confirmação para subir a 5 V)."""
    if len(p) < 3:
        raise ProtocolError("VOLT_RESP curto")
    return {"voltage_select": bool(p[0]), "voltage": {1: "3v3", 2: "5v"}.get(p[1], "5v-fixed"), "chosen": bool(p[2])}


def parse_detect_resp(p: bytes) -> dict:
    if len(p) < 12:
        raise ProtocolError("DETECT_RESP curto")
    system, status, rom, save, stype, n = struct.unpack_from("<BBIIBB", p)
    name = p[12:12 + n].decode("ascii", "replace")
    return {"system": system, "status": status, "rom_size": rom, "save_size": save,
            "save_type": stype, "name": name}


def parse_begin(p: bytes) -> tuple[int, int, int]:
    if len(p) < 7:
        raise ProtocolError("BEGIN curto")
    return struct.unpack_from("<BIH", p)  # tipo_dado, tamanho, bloco


def parse_data(p: bytes) -> tuple[int, bytes]:
    if len(p) < 4:
        raise ProtocolError("DATA curto")
    return struct.unpack_from("<I", p)[0], p[4:]


def parse_end(p: bytes) -> tuple[int, int]:
    if len(p) < 8:
        raise ProtocolError("END curto")
    return struct.unpack_from("<II", p)


def parse_progress(p: bytes) -> tuple[int, int, int]:
    """PROGRESSO: (offset, total, etapa). O 9º byte é opcional (firmware sem etapa: 0); total 0 = desconhecido."""
    if len(p) < 8:
        raise ProtocolError("PROGRESSO curto")
    off, total = struct.unpack_from("<II", p)
    return off, total, p[8] if len(p) >= 9 else STAGE_NONE


def parse_offset(p: bytes) -> int:
    if len(p) < 4:
        raise ProtocolError("ACK/NAK curto")
    return struct.unpack_from("<I", p)[0]


def parse_error(p: bytes) -> DeviceError:
    code, n = struct.unpack_from("<HB", p) if len(p) >= 3 else (0, 0)
    return DeviceError(code, p[3:3 + n].decode("ascii", "replace"))


# padrão do modo MOCK (docs/referencia/protocolo.md, seção 9)
MOCK_SIZE = 32768


def mock_byte(i: int) -> int:
    return (i * 7 + (i >> 8)) & 0xFF


def mock_data(size: int = MOCK_SIZE) -> bytes:
    return bytes(mock_byte(i) for i in range(size))


def pin_name(pin: int) -> str:
    """Nome do pino na numeração do Arduino Mega: 54 em diante são A0... (como o autoteste do OSCR imprime)."""
    return f"A{pin - 54}" if pin >= 54 else f"D{pin}"


def parse_selftest_resp(p: bytes) -> dict:
    """SELFTEST_RESP: `ok` se nada foi achado; `truncated` se houve mais achados do que cabem na resposta.
    Cada achado: `{"kind": "gnd"|"pair"|"pullup"|"clockgen", "pins": [nomes]}`."""
    if len(p) < 2 or len(p) < 2 + p[1] * 3:
        raise ProtocolError("SELFTEST_RESP curto")
    kinds = {ST_GND: "gnd", ST_PAIR: "pair", ST_NO_PULLUP: "pullup", ST_NO_CLOCKGEN: "clockgen"}
    findings = []
    for i in range(p[1]):
        k, a, b = p[2 + i * 3: 5 + i * 3]
        pins = {ST_GND: [a], ST_PAIR: [a, b], ST_NO_PULLUP: [a]}.get(k, [])
        findings.append({"kind": kinds.get(k, f"unknown{k}"), "pins": [pin_name(x) for x in pins]})
    return {"ok": not findings and not p[0], "truncated": bool(p[0]), "findings": findings}
