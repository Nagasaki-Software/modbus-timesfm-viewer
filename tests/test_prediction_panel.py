from app.ui.prediction_panel import PredictionPanel


def test_horizon_and_interval_signals(qtbot):
    panel = PredictionPanel()
    qtbot.addWidget(panel)
    h_captured = []
    i_captured = []
    in_captured = []
    panel.horizonChanged.connect(h_captured.append)
    panel.intervalChanged.connect(i_captured.append)
    panel.inputIntervalChanged.connect(in_captured.append)
    panel.horizon_slider.setValue(120)
    panel.interval_slider.setValue(10)
    panel.input_interval_slider.setValue(30)
    assert h_captured[-1] == 120
    assert i_captured[-1] == 10
    assert in_captured[-1] == 30


def test_show_inference_time(qtbot):
    panel = PredictionPanel()
    qtbot.addWidget(panel)
    panel.show_inference_time(1.234)
    assert "1.23" in panel.inference_label.text()


def test_input_interval_clamped_to_poll(qtbot):
    """取得周期未満の入力周期は受け付けない。設定すると取得周期にクランプ。"""
    panel = PredictionPanel()
    qtbot.addWidget(panel)
    panel.set_poll_interval(5)
    assert panel.input_interval_slider.minimum() == 5
    panel.input_interval_slider.setValue(2)
    assert panel.input_interval_slider.value() == 5


def test_subsecond_poll_interval(qtbot):
    panel = PredictionPanel()
    qtbot.addWidget(panel)
    panel.set_poll_interval(0.5)
    assert panel.input_interval_slider.minimum() == 1
    panel.input_interval_slider.setValue(3)
    assert "6点に1点" in panel.input_interval_label.text()
