from app.ui.connection_panel import ConnectionPanel


def test_emits_connect_with_input(qtbot):
    panel = ConnectionPanel()
    qtbot.addWidget(panel)
    panel.host_edit.setText("192.168.1.10")
    panel.port_edit.setText("502")
    panel.unit_edit.setText("1")
    captured = []
    panel.connectRequested.connect(lambda h, p, u: captured.append((h, p, u)))
    panel.connect_btn.click()
    assert captured[-1] == ("192.168.1.10", 502, 1)


def test_status_label_reflects_state(qtbot):
    panel = ConnectionPanel()
    qtbot.addWidget(panel)
    panel.set_status("connected", "192.168.1.10:502")
    assert "接続" in panel.status_label.text()
