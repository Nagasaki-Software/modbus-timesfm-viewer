from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np


class AppSignals(QObject):
    # ModbusClient → UI
    sampleReceived = pyqtSignal(int, float, float)        # ch, ts, value
    connectionStatusChanged = pyqtSignal(str, str)        # state, message
    # Predictor → UI
    predictionReady = pyqtSignal(int, float, float, object, float)
    # ch, last_ts, input_interval_sec, horizon_values(np.ndarray), inference_time
    predictorStatusChanged = pyqtSignal(str, str)  # kind, message
