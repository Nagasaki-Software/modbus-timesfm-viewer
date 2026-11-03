import threading
import time
import pytest
from pymodbus.server import StartTcpServer, ServerStop
from pymodbus.simulator.simdata import SimData, DataType
from pymodbus.simulator.simdevice import SimDevice
from app.config import ChannelConfig
from app.modbus_client import ModbusClient, decode_value
from app.ring_buffer import RingBuffer


@pytest.fixture
def fake_device():
    # float32 ABCD で 25.5 をレジスタ 0,1 に書き込む
    import struct
    raw = struct.pack(">f", 25.5)
    reg0 = int.from_bytes(raw[0:2], "big")
    reg1 = int.from_bytes(raw[2:4], "big")
    co = SimData(address=0, count=1, values=False, datatype=DataType.BITS)
    di = SimData(address=0, count=1, values=False, datatype=DataType.BITS)
    ir = SimData(address=0, count=1, values=0, datatype=DataType.REGISTERS)
    hr = SimData(address=0, count=2, values=[reg0, reg1], datatype=DataType.REGISTERS)
    dev = SimDevice(0, simdata=([co], [di], [hr], [ir]))
    t = threading.Thread(target=StartTcpServer, kwargs={"context": dev, "address": ("127.0.0.1", 15020)}, daemon=True)
    t.start()
    time.sleep(0.3)
    yield dev
    ServerStop()


def test_polls_and_pushes_to_buffer(fake_device):
    buf = RingBuffer(capacity=10)
    channels = [ChannelConfig(ch=1, name="t1", address=0, data_type="float32",
                              byte_order="ABCD", color="#fff", visible=True, predict_target=True)]
    client = ModbusClient(host="127.0.0.1", port=15020, unit_id=1,
                          poll_interval_sec=0.2, channels=channels, buffer=buf)
    client.start()
    time.sleep(0.6)
    client.stop()
    _, vals = buf.latest(1, 10)
    assert len(vals) >= 2
    assert all(abs(v - 25.5) < 0.01 for v in vals)
