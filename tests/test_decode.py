import struct
import math
import pytest
from app.modbus_client import decode_value


def regs_from_float(value: float, order: str) -> list[int]:
    raw = struct.pack(">f", value)  # ABCD
    b = {
        "ABCD": raw,
        "CDAB": raw[2:4] + raw[0:2],
        "BADC": raw[1:2] + raw[0:1] + raw[3:4] + raw[2:3],
        "DCBA": raw[::-1],
    }[order]
    return [int.from_bytes(b[0:2], "big"), int.from_bytes(b[2:4], "big")]


@pytest.mark.parametrize("order", ["ABCD", "CDAB", "BADC", "DCBA"])
def test_decode_float32(order):
    regs = regs_from_float(123.456, order)
    v = decode_value(regs, "float32", order)
    assert math.isclose(v, 123.456, rel_tol=1e-5)


def test_decode_int16_signed():
    assert decode_value([0xFFFF], "int16", "ABCD") == -1
    assert decode_value([0x7FFF], "int16", "ABCD") == 32767


def test_decode_int32_signed_cdab():
    regs = [0x5678, 0x1234]  # CDAB 順で 0x12345678
    assert decode_value(regs, "int32", "CDAB") == 0x12345678
