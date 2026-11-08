from pathlib import Path
from app.config import Config, ChannelConfig


def test_save_and_load_roundtrip(tmp_path: Path):
    cfg = Config(
        host="192.168.1.10",
        port=502,
        unit_id=1,
        poll_interval_sec=1.0,
        channels=[
            ChannelConfig(ch=1, name="温度1", address=0x0000,
                          data_type="float32", byte_order="CDAB",
                          color="#ff0000", visible=True, predict_target=True,
                          decimals=1),
        ],
        horizon_sec=60,
        predict_interval_sec=5.0,
        predict_input_interval_sec=10.0,
        y_auto=False, y_min=-5.0, y_max=50.0, y_tick=5.0,
    )
    path = tmp_path / "config.toml"
    cfg.save(path)
    loaded = Config.load(path)
    assert loaded == cfg


def test_load_missing_file_returns_defaults(tmp_path: Path):
    cfg = Config.load(tmp_path / "missing.toml")
    assert cfg.host == ""
    assert cfg.port == 502
    assert cfg.unit_id == 1
    assert cfg.channels == []


def test_unknown_keys_are_ignored(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text('host = "1.2.3.4"\nfuture_key = 1\n'
                    '[[channels]]\nch = 1\nname = "a"\naddress = 0\ndata_type = "float32"\n'
                    'byte_order = "ABCD"\ncolor = "#fff"\nvisible = true\npredict_target = true\n'
                    'extra = "x"\n', encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.host == "1.2.3.4"
    assert len(cfg.channels) == 1
    assert cfg.channels[0].decimals == 2  # 古い設定ファイルには桁数が無い
    assert cfg.y_auto is True


def test_broken_file_falls_back_to_defaults(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text("this is = = not toml", encoding="utf-8")
    cfg = Config.load(path)
    assert cfg == Config()
    assert (tmp_path / "config.toml.broken").exists()
