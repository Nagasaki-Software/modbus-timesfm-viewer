from app.config import ChannelConfig
from app.ui.channel_panel import ChannelPanel


def test_panel_populates_from_config(qtbot):
    ch = ChannelConfig(ch=1, name="温度1", address=0, data_type="float32",
                       byte_order="ABCD", color="#ff0000", visible=True, predict_target=True)
    panel = ChannelPanel()
    qtbot.addWidget(panel)
    panel.set_channels([ch])
    assert panel.table.rowCount() == 1
    assert panel.table.item(0, 1).text() == "1"
    assert panel.table.item(0, 2).text() == "温度1"


def test_predict_target_only_one(qtbot):
    chs = [
        ChannelConfig(1, "t1", 0, "float32", "ABCD", "#f00", True, True),
        ChannelConfig(2, "t2", 2, "float32", "ABCD", "#0f0", True, False),
    ]
    panel = ChannelPanel()
    qtbot.addWidget(panel)
    panel.set_channels(chs)
    panel.set_predict_target(2)
    assert panel.get_predict_target() == 2
    chs_out = panel.get_channels()
    assert sum(1 for c in chs_out if c.predict_target) == 1


def test_duplicate_channel_number_rejected(qtbot, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    warned = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: warned.append(a))
    panel = ChannelPanel()
    qtbot.addWidget(panel)
    panel.set_channels([ChannelConfig(1, "t1", 0, "float32", "ABCD", "#f00", True, True)])
    assert panel._is_duplicate(1, skip_row=-1) is True
    assert panel._is_duplicate(1, skip_row=0) is False
    assert panel._is_duplicate(2, skip_row=-1) is False
    assert len(warned) == 1
