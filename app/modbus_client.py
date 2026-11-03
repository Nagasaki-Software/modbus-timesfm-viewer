from __future__ import annotations
import struct


def _bytes_from_regs(regs: list[int], order: str) -> bytes:
    if len(regs) == 1:
        return regs[0].to_bytes(2, "big", signed=False)
    raw = regs[0].to_bytes(2, "big") + regs[1].to_bytes(2, "big")  # ABCD
    if order == "ABCD":
        return raw
    if order == "CDAB":
        return raw[2:4] + raw[0:2]
    if order == "BADC":
        return raw[1:2] + raw[0:1] + raw[3:4] + raw[2:3]
    if order == "DCBA":
        return raw[::-1]
    raise ValueError(f"unknown byte order: {order}")


def decode_value(regs: list[int], data_type: str, byte_order: str) -> float:
    if data_type == "int16":
        return float(int.from_bytes(_bytes_from_regs(regs, byte_order), "big", signed=True))
    if data_type == "int32":
        return float(int.from_bytes(_bytes_from_regs(regs, byte_order), "big", signed=True))
    if data_type == "float32":
        return float(struct.unpack(">f", _bytes_from_regs(regs, byte_order))[0])
    raise ValueError(f"unknown data type: {data_type}")


import threading
import time
import logging
from pymodbus.client import ModbusTcpClient
from app.config import ChannelConfig
from app.ring_buffer import RingBuffer

log = logging.getLogger(__name__)


class ModbusClient:
    def __init__(self, host: str, port: int, unit_id: int,
                 poll_interval_sec: float,
                 channels: list[ChannelConfig],
                 buffer: RingBuffer,
                 on_status=None):
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._interval = poll_interval_sec
        self._channels = channels
        self._buffer = buffer
        self._on_status = on_status or (lambda s, msg="": None)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._client: ModbusTcpClient | None = None
        self._consecutive_failures = 0
        self._backoff = 1.0
        self._last_error = ""

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._client:
            self._client.close()
            self._client = None

    def _connect(self) -> bool:
        if self._client:
            self._client.close()
        self._client = ModbusTcpClient(self._host, port=self._port, timeout=2.0)
        ok = self._client.connect()
        if ok:
            self._on_status("connected", f"{self._host}:{self._port}")
            self._consecutive_failures = 0
            self._backoff = 1.0
        else:
            self._on_status("disconnected", "connect failed")
        return ok

    def _read_channel(self, ch: ChannelConfig) -> float | None:
        count = 1 if ch.data_type == "int16" else 2
        try:
            rr = self._client.read_holding_registers(ch.address, count=count, device_id=self._unit_id)
            if rr.isError():
                self._last_error = f"ch{ch.ch} addr={ch.address}: {rr}"
                log.warning("modbus error response: %s", self._last_error)
                return None
            return decode_value(list(rr.registers), ch.data_type, ch.byte_order)
        except Exception as e:
            self._last_error = f"ch{ch.ch}: {e}"
            log.warning("read failed ch=%s: %s", ch.ch, e)
            return None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            if not self._client or not self._client.connected:
                if not self._connect():
                    self._on_status("retrying", f"backoff {self._backoff:.0f}s")
                    self._stop_event.wait(self._backoff)
                    self._backoff = min(self._backoff * 2, 8.0)
                    continue
            success_any = False
            for ch in self._channels:
                v = self._read_channel(ch)
                ts = time.time()
                if v is None:
                    continue
                self._buffer.push(ch.ch, ts, v)
                success_any = True
            if success_any:
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1
                if self._consecutive_failures >= 3:
                    self._on_status("disconnected", f"3回連続で読取失敗 ({self._last_error})")
                    self._client.close()
                    self._client = None
            self._stop_event.wait(self._interval)
