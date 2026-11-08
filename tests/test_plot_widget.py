from app.ui.plot_widget import PlotWidget
import numpy as np


def test_configure_and_append(qtbot):
    w = PlotWidget()
    qtbot.addWidget(w)
    w.configure_channel(1, "t1", "#ff0000")
    w.append_sample(1, 0.0, 1.0)
    w.append_sample(1, 1.0, 2.0)
    w.set_prediction(1, last_ts=1.0, input_interval=1.0,
                     horizon_values=np.array([3.0, 4.0, 5.0]))
    assert 1 in w._actual
    assert 1 in w._predicted


def test_value_label_shows_latest_with_decimals(qtbot):
    w = PlotWidget()
    qtbot.addWidget(w)
    w.configure_channel(1, "温度", "#ff0000", decimals=1)
    assert "—" in w._actual[1]["label"].text()
    w.append_sample(1, 0.0, 23.456)
    assert "23.5" in w._actual[1]["label"].text()
    w.configure_channel(1, "温度", "#ff0000", decimals=0)
    assert "<b>23</b>" in w._actual[1]["label"].text()
    w.set_visible(1, False)
    assert w._actual[1]["label"].isHidden()
    w.remove_channel(1)
    assert 1 not in w._actual


def test_manual_y_axis_fixes_range(qtbot):
    w = PlotWidget()
    qtbot.addWidget(w)
    w.configure_channel(1, "t1", "#ff0000")
    w.set_y_axis(False, -10.0, 50.0, 5.0)
    w.append_sample(1, 0.0, 1000.0)  # 範囲外の値が来ても縦軸は動かない
    y_range = w._plot.getPlotItem().getViewBox().viewRange()[1]
    assert y_range[0] < -10.0 < -9.0 and 50.0 < y_range[1] < 51.5  # 少しだけ余白を足す
    assert w._plot.getAxis("left")._tickSpacing == [(5.0, -10.0)]
    w.set_y_axis(True, -10.0, 50.0, 5.0)
    assert w._plot.getAxis("left")._tickSpacing is None
