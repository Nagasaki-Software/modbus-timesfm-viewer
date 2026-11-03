# modbus-timesfm-viewer

Modbus-TCP に対応した計測機器・データロガーから測定値を取り込み、Google Research の時系列予測モデル **TimesFM 2.5** で少し先の値を予測して、実測値（実線）と予測値（破線）をリアルタイムにグラフ表示する Windows デスクトップアプリです。

> **免責事項**
> - 本ソフトウェアは「現状のまま」提供され、いかなる保証もありません。
> - 本ソフトウェアの使用により生じたいかなる損害についても、作者は責任を負いません。
> - 予測値は AI による推定であり、正確性は保証されません。設備の運転・安全の判断や、法令にもとづく記録には、本ソフトウェアだけを使わないでください。
> - 本ソフトウェアは Google とは関係のない、個人による非公式のツールです。

## 主な機能

- Modbus-TCP 機器の保持レジスタ（int16 / int32 / float32、4種類のバイト順）を定周期で読み取り
- 複数チャネルの実測値をリアルタイムにグラフ表示（表示色・表示/非表示を切替）
- 選んだ1チャネルを TimesFM 2.5 で予測し、破線で重ねて表示
- 予測の長さ（ホライズン）、実行間隔、入力の間引き周期を画面で調整
- 接続先・チャネル設定は自動保存

## 動作環境

- Windows 10 / 11（64bit）
- CPU のみで動作します（GPU 不要）
- 初回のモデルダウンロード時のみインターネット接続が必要です

## 使い方（配布版）

1. [Releases](../../releases) から `modbus-timesfm-viewer-v<版>.zip` をダウンロードします。
   緑色の「Code」ボタンの「Download ZIP」や「Source code (zip)」は開発用のソースなので選ばないでください。
2. ダウンロードした zip を右クリック →「プロパティ」→「許可する」にチェックを入れて「OK」を押します。
3. zip を展開します。`modbus-timesfm-viewer.exe` と `models` フォルダは同じ場所に置いたままにしてください。
4. `modbus-timesfm-viewer.exe` をダブルクリックして起動します。
5. 画面左で接続する機器の IP アドレス・ポート・ユニット ID を入力し、「チャネル」で読み取るレジスタを登録します。
6. 「接続」を押すと、グラフに実測値が表示されます。データが 32 点たまると予測の破線が表示されます。

### AI モデルについて

配布 zip には AI モデル本体（約 882MB）を含めていません。初回に「接続」を押すと、モデル [google/timesfm-2.5-200m-pytorch](https://huggingface.co/google/timesfm-2.5-200m-pytorch) が `models` フォルダへ自動でダウンロードされます（数分かかります）。2回目以降はインターネットに接続しなくても使えます。

インターネットに接続できない PC で使う場合は、別の PC でダウンロード済みの `models` フォルダごとコピーしてください。詳しくは zip 内の `models/モデルのダウンロード方法.txt` を参照してください。

### 設定とログの保存場所

- 設定：`%USERPROFILE%\.modbus-timesfm-viewer\config.toml`（最初は存在せず、「接続」やチャネルの編集で作成されます）
- ログ：`%USERPROFILE%\.modbus-timesfm-viewer\logs\app.log`

## 開発者向け

### 環境構築

Python 3.11 が必要です（TimesFM / PyTorch の対応のため。3.14 では動作を確認していません）。

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -e ".[dev]"
```

### テスト

```bash
QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest
```

注意：`tests/test_main_window.py` は実際の設定ファイル（`%USERPROFILE%\.modbus-timesfm-viewer\config.toml`）を読み書きします。

### EXE のビルド

```bash
.venv/Scripts/python.exe -m PyInstaller modbus-timesfm-viewer.spec --clean --noconfirm
```

`dist/modbus-timesfm-viewer.exe` が作成されます。配布するときは、同じ場所に空の `models` フォルダを置いてください。

## ライセンス

本ソフトウェアは [GNU General Public License v3.0](LICENSE) のもとで公開しています。

Copyright (C) 2026 Nagasaki-Software

利用している外部ライブラリと AI モデルのライセンスは [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。GUI に GPL-3.0 の PyQt6 を使っているため、本ソフトウェアも GPL-3.0 としています。
