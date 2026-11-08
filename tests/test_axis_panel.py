from app.ui.axis_panel import AxisPanel


def test_auto_toggle_and_apply(qtbot):
    p = AxisPanel()
    qtbot.addWidget(p)
    p.set_values(True, 0.0, 100.0, 10.0)
    assert not p.min_spin.isEnabled()
    got = []
    p.axisChanged.connect(lambda *a: got.append(a))
    p.auto_check.setChecked(False)  # 手動にした時点で今の値を適用する
    assert got[-1] == (False, 0.0, 100.0, 10.0)
    p.max_spin.setValue(200.0)
    p.apply_btn.click()
    assert got[-1] == (False, 0.0, 200.0, 10.0)
    p.auto_check.setChecked(True)
    assert got[-1][0] is True


def test_invalid_values_are_rejected(qtbot):
    p = AxisPanel()
    qtbot.addWidget(p)
    p.set_values(False, 0.0, 100.0, 10.0)
    got = []
    p.axisChanged.connect(lambda *a: got.append(a))
    p.min_spin.setValue(100.0)
    p.apply_btn.click()
    assert got == [] and "最大値" in p.error_label.text()
    p.min_spin.setValue(0.0)
    p.tick_spin.setValue(0.0)
    p.apply_btn.click()
    assert got == [] and "目盛り間隔" in p.error_label.text()
    p.tick_spin.setValue(0.5)  # 200 本になる
    p.apply_btn.click()
    assert got == [] and "100 本" in p.error_label.text()
    p.tick_spin.setValue(20.0)
    p.apply_btn.click()
    assert got == [(False, 0.0, 100.0, 20.0)] and p.error_label.text() == ""
