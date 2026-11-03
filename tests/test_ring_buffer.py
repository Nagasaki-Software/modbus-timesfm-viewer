import threading
import numpy as np
from app.ring_buffer import RingBuffer


def test_push_and_latest_basic():
    buf = RingBuffer(capacity=4)
    for i in range(3):
        buf.push(ch=1, ts=float(i), value=float(i * 10))
    ts, val = buf.latest(ch=1, n=3)
    assert np.allclose(ts, [0.0, 1.0, 2.0])
    assert np.allclose(val, [0.0, 10.0, 20.0])


def test_capacity_overflow_drops_oldest():
    buf = RingBuffer(capacity=3)
    for i in range(5):
        buf.push(ch=1, ts=float(i), value=float(i))
    ts, val = buf.latest(ch=1, n=10)
    assert np.allclose(ts, [2.0, 3.0, 4.0])
    assert np.allclose(val, [2.0, 3.0, 4.0])


def test_multiple_channels_isolated():
    buf = RingBuffer(capacity=10)
    buf.push(1, 0.0, 100.0)
    buf.push(2, 0.0, 200.0)
    _, v1 = buf.latest(1, 5)
    _, v2 = buf.latest(2, 5)
    assert v1.tolist() == [100.0]
    assert v2.tolist() == [200.0]


def test_thread_safety():
    buf = RingBuffer(capacity=10000)

    def push_loop(ch):
        for i in range(1000):
            buf.push(ch, float(i), float(i))

    threads = [threading.Thread(target=push_loop, args=(c,)) for c in (1, 2, 3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for ch in (1, 2, 3):
        ts, _ = buf.latest(ch, 1000)
        assert len(ts) == 1000


def test_clear_removes_all_channels():
    buf = RingBuffer(capacity=4)
    buf.push(1, 0.0, 1.0)
    buf.push(2, 0.0, 2.0)
    buf.clear()
    assert len(buf.latest(1, 5)[0]) == 0
    assert len(buf.latest(2, 5)[0]) == 0
