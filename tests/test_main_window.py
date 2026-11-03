from app.ui.main_window import MainWindow


def test_main_window_constructs(qtbot):
    win = MainWindow(start_workers=False)
    qtbot.addWidget(win)
    win.show()
    assert win.menuBar() is not None
    assert win.connection_panel is not None
    assert win.channel_panel is not None
    assert win.prediction_panel is not None
    assert win.plot_widget is not None


def test_params_follow_ui_and_pump_is_not_duplicated(qtbot, monkeypatch):
    from app.config import ChannelConfig
    win = MainWindow(start_workers=False)
    qtbot.addWidget(win)
    win.channel_panel.set_channels([
        ChannelConfig(1, "a", 0, "float32", "ABCD", "#f00", True, True)])
    win.prediction_panel.horizon_slider.setValue(120)
    win._sync_params()
    assert win._params["horizon"] == 120
    assert win._params["target"] == 1

    got = []
    win._signals.sampleReceived.connect(lambda ch, ts, v: got.append((ch, ts, v)))
    win._buffer.push(1, 1.0, 10.0)
    win._buffer.push(1, 2.0, 20.0)
    win._start_buffer_pump()
    win._start_buffer_pump()  # 再接続を模擬
    qtbot.wait(500)
    assert got == [(1, 1.0, 10.0), (1, 2.0, 20.0)]  # 二重送出なし・取りこぼしなし
    win._pump_timer.stop()
