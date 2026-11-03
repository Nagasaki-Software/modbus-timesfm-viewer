from __future__ import annotations
import threading
from collections import deque
import numpy as np


class RingBuffer:
    def __init__(self, capacity: int = 2048):
        self._capacity = capacity
        self._lock = threading.Lock()
        self._data: dict[int, deque[tuple[float, float]]] = {}

    def push(self, ch: int, ts: float, value: float) -> None:
        with self._lock:
            dq = self._data.get(ch)
            if dq is None:
                dq = deque(maxlen=self._capacity)
                self._data[ch] = dq
            dq.append((ts, value))

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def latest(self, ch: int, n: int) -> tuple[np.ndarray, np.ndarray]:
        with self._lock:
            dq = self._data.get(ch)
            if dq is None or len(dq) == 0:
                return np.empty(0), np.empty(0)
            items = list(dq)[-n:]
        ts_arr = np.fromiter((x[0] for x in items), dtype=float, count=len(items))
        val_arr = np.fromiter((x[1] for x in items), dtype=float, count=len(items))
        return ts_arr, val_arr
