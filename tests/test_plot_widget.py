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
