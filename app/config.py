from __future__ import annotations
from dataclasses import dataclass, field, asdict, fields
import logging
from pathlib import Path
import tomllib
import tomli_w

log = logging.getLogger(__name__)


@dataclass
class ChannelConfig:
    ch: int
    name: str
    address: int
    data_type: str  # "int16" | "int32" | "float32"
    byte_order: str  # "ABCD" | "CDAB" | "BADC" | "DCBA"
    color: str       # "#rrggbb"
    visible: bool
    predict_target: bool
    decimals: int = 2  # グラフ下段に出す値の小数桁数


@dataclass
class Config:
    host: str = ""
    port: int = 502
    unit_id: int = 1
    poll_interval_sec: float = 1.0
    channels: list[ChannelConfig] = field(default_factory=list)
    horizon_sec: int = 60
    predict_interval_sec: float = 5.0
    predict_input_interval_sec: float = 1.0  # TimesFM 入力周期（秒）。poll_interval_sec 以上であること
    y_auto: bool = True  # 縦軸をデータに合わせて自動で広げる
    y_min: float = 0.0
    y_max: float = 100.0
    y_tick: float = 10.0  # 目盛りの間隔
    window_geometry: list[int] = field(default_factory=lambda: [100, 100, 1200, 800])

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            return cls()
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
            ch_keys = {f.name for f in fields(ChannelConfig)}
            channels = [ChannelConfig(**{k: v for k, v in c.items() if k in ch_keys})
                        for c in data.pop("channels", [])]
            keys = {f.name for f in fields(cls)} - {"channels"}
            return cls(channels=channels, **{k: v for k, v in data.items() if k in keys})
        except (tomllib.TOMLDecodeError, TypeError, OSError) as e:
            # 壊れた設定で起動不能にならないよう、退避してデフォルトで起動する
            log.warning("config load failed (%s); using defaults", e)
            try:
                path.replace(path.with_suffix(".toml.broken"))
            except OSError:
                pass
            return cls()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        with path.open("wb") as f:
            tomli_w.dump(data, f)
