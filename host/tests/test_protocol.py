# SPDX-License-Identifier: GPL-3.0-or-later
"""Framing, CRC e (de)serialização. Os vetores batem com docs/protocolo.md, seção 9."""
import struct

import pytest

from oscr_host import protocol as P


def test_crc32_vetores():
    assert P.crc32(b"123456789") == 0xCBF43926
    assert P.crc32(b"") == 0
    assert P.crc32(b"OSCR") == 0xD2F82B80


def test_quadro_info_bytes_exatos():
    assert P.encode_frame(P.T_INFO, 1).hex(" ").upper() == "A5 5A 01 01 00 00 4E D2 3A 98"


def test_roundtrip_todos_os_tamanhos_de_payload():
    dec = P.FrameDecoder()
    for n in (0, 1, 7, 512, 1024):
        pl = bytes(i & 0xFF for i in range(n))
        frames = dec.feed(P.encode_frame(P.T_DATA, 200 + n % 50, pl))
        assert len(frames) == 1 and frames[0].payload == pl and frames[0].type == P.T_DATA


def test_payload_maior_que_o_limite():
    with pytest.raises(P.ProtocolError):
        P.encode_frame(P.T_DATA, 0, bytes(1025))


def test_decodificador_em_pedacos_de_1_byte():
    raw = P.encode_frame(P.T_DETECT, 9, b"\x01") + P.encode_frame(P.T_INFO, 10)
    dec, out = P.FrameDecoder(), []
    for b in raw:
        out += dec.feed(bytes([b]))
    assert [(f.type, f.seq) for f in out] == [(P.T_DETECT, 9), (P.T_INFO, 10)]


def test_crc_ruim_descarta_e_ressincroniza():
    good = P.encode_frame(P.T_INFO, 5)
    bad = bytearray(P.encode_frame(P.T_DETECT, 6, b"\x01"))
    bad[6] ^= 0x01  # estraga o payload
    dec = P.FrameDecoder()
    out = dec.feed(b"\x00\xA5\xFF" + bytes(bad) + good)
    assert [f.seq for f in out] == [5]
    assert dec.bad_frames >= 1


def test_len_invalido_nao_trava():
    dec = P.FrameDecoder()
    junk = P.MAGIC + struct.pack("<BBH", 1, 1, 60000)
    out = dec.feed(junk + P.encode_frame(P.T_INFO, 3))
    assert [f.seq for f in out] == [3]


def test_magia_partida_entre_chamadas():
    raw = P.encode_frame(P.T_INFO, 4)
    dec = P.FrameDecoder()
    assert dec.feed(raw[:1]) == []
    assert [f.seq for f in dec.feed(raw[1:])] == [4]


def test_parsers():
    assert P.parse_detect_resp(bytes([1, 0]) + (1024).to_bytes(4, "little") + (8).to_bytes(4, "little")
                               + bytes([1, 3]) + b"ABC") == {
        "system": 1, "status": 0, "rom_size": 1024, "save_size": 8, "save_type": 1, "name": "ABC", "attempts": 1}
    assert P.parse_begin(bytes([1]) + (100).to_bytes(4, "little") + (512).to_bytes(2, "little")) == (1, 100, 512)
    off, data = P.parse_data(P.build_data(1024, b"xyz"))
    assert (off, data) == (1024, b"xyz")
    e = P.parse_error((6).to_bytes(2, "little") + bytes([2]) + b"hi")
    assert e.code == 6 and e.text == "hi"


def test_padrao_mock():
    d = P.mock_data()
    assert len(d) == 32768 and d[0] == 0 and d[1] == 7 and d[256] == (256 * 7 + 1) & 0xFF
