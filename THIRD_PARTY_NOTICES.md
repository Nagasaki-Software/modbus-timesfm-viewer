# Third-Party Notices

本ソフトウェアは、以下の外部ライブラリと AI モデルを利用しています。各ライブラリの著作権は、それぞれの作者に帰属します。

## リポジトリに含まれるもの

このリポジトリのソースコードには、外部ライブラリのコードを含めていません。外部ライブラリは `pip install` でインストールされます（`pyproject.toml` を参照）。

## 配布版 EXE に同梱されるもの

配布版の `modbus-timesfm-viewer.exe` は PyInstaller で作成しており、次のライブラリと Python 本体を同梱しています。版数は、配布版を作成したときのものです。

### 主要なライブラリ

| ライブラリ | 版 | ライセンス | 入手先 |
|---|---|---|---|
| PyQt6 | 6.11.0 | GPL-3.0-only | https://www.riverbankcomputing.com/software/pyqt/ |
| Qt 6（PyQt6-Qt6） | 6.11.1 | LGPL-3.0 | https://www.qt.io/ |
| PyQt6-sip | 13.11.1 | BSD-2-Clause | https://github.com/Python-SIP/sip |
| pyqtgraph | 0.14.0 | MIT | https://github.com/pyqtgraph/pyqtgraph |
| pymodbus | 3.13.1 | BSD-3-Clause | https://github.com/pymodbus-dev/pymodbus |
| timesfm | 2.0.1 | Apache-2.0 | https://github.com/google-research/timesfm |
| PyTorch（torch） | 2.12.1 | BSD-3-Clause | https://pytorch.org |
| NumPy | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | https://numpy.org |
| huggingface_hub | 1.20.1 | Apache-2.0 | https://github.com/huggingface/huggingface_hub |
| safetensors | 0.8.0 | Apache-2.0 | https://github.com/huggingface/safetensors |
| tomli-w | 1.2.0 | MIT | https://github.com/hukkin/tomli-w |
| Python | 3.11.15 | PSF-2.0 | https://www.python.org |
| PyInstaller ブートローダー | 6.21.0 | GPL-2.0-or-later（同梱物の配布を許可する例外付き） | https://pyinstaller.org |

### 上記が内部で利用するライブラリ

| ライブラリ | 版 | ライセンス |
|---|---|---|
| annotated-doc | 0.0.4 | MIT |
| anyio | 4.14.0 | MIT |
| certifi | 2026.6.17 | MPL-2.0 |
| click | 8.4.1 | BSD-3-Clause |
| colorama | 0.4.6 | BSD-3-Clause |
| filelock | 3.29.4 | MIT |
| fsspec | 2026.6.0 | BSD-3-Clause |
| h11 | 0.16.0 | MIT |
| hf-xet | 1.5.1 | Apache-2.0 |
| httpcore | 1.0.9 | BSD-3-Clause |
| httpx | 0.28.1 | BSD-3-Clause |
| idna | 3.18 | BSD-3-Clause |
| Jinja2 | 3.1.6 | BSD-3-Clause |
| markdown-it-py | 4.2.0 | MIT |
| MarkupSafe | 3.0.3 | BSD-3-Clause |
| mdurl | 0.1.2 | MIT |
| mpmath | 1.3.0 | BSD-3-Clause |
| networkx | 3.6.1 | BSD-3-Clause |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause |
| Pygments | 2.20.0 | BSD-2-Clause |
| PyYAML | 6.0.3 | MIT |
| rich | 15.0.0 | MIT |
| setuptools | 81.0.0 | MIT |
| shellingham | 1.5.4 | ISC |
| sympy | 1.14.0 | BSD-3-Clause |
| tqdm | 4.68.3 | MPL-2.0 AND MIT |
| typer | 0.25.1 | MIT |
| typing_extensions | 4.15.0 | PSF-2.0 |

### Qt（LGPL-3.0）について

Qt 6 は LGPL-3.0 のもとで利用しています。Qt のソースコードは https://download.qt.io/ から入手できます。本ソフトウェアの全ソースコードと、配布版 EXE を作り直す手順（README の「EXE のビルド」）を公開しているので、利用者は Qt を差し替えて EXE を作り直すことができます。

## 配布版に含まれず、初回起動時にダウンロードされるもの

| AI モデル | ライセンス | 入手先 |
|---|---|---|
| TimesFM 2.5（google/timesfm-2.5-200m-pytorch） | Apache-2.0 | https://huggingface.co/google/timesfm-2.5-200m-pytorch |

TimesFM 3.0 以降のモデルは非商用ライセンス（timesfm-non-commercial-license-v1.0）で公開されているため、本ソフトウェアでは使用していません。

## ライセンス本文

- GPL-3.0：本リポジトリの [LICENSE](LICENSE)
- LGPL-3.0：https://www.gnu.org/licenses/lgpl-3.0.html
- Apache-2.0：https://www.apache.org/licenses/LICENSE-2.0
- MIT / BSD などの本文：各ライブラリの入手先にある LICENSE ファイル
