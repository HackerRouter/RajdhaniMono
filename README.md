# Rajdhani Mono

[English](README.en.md) · [字体文件](fonts/ttf) · [许可](LICENSE)

Rajdhani Mono 是基于 [Rajdhani](https://github.com/itfoundry/rajdhani) 制作的非官方等宽字体，面向终端和代码编辑器。它保留了原字体窄方形、圆角和直线端点的风格，将字符调整到统一的字格中。

当前版本：**v0.2**。字体软件和构建配方使用 **SIL Open Font License 1.1**。

![Rajdhani Mono 字体样张](docs/images/preview.png)

## 安装与试用

下载仓库 ZIP 或克隆仓库，然后安装 [`fonts/ttf/`](fonts/ttf) 中的五个 TTF 文件。在终端或编辑器中选择 **Rajdhani Mono**，建议从 **Medium 500** 开始试用。部分应用会将它显示为单独的 **Rajdhani Mono Medium** 字体家族。

- **Windows**：选中 TTF 文件，右键安装。
- **macOS**：用字体册打开 TTF 文件并安装。
- **Linux**：在仓库根目录执行以下命令，然后重新打开应用的字体选择窗口。

```sh
mkdir -p "${XDG_DATA_HOME:-$HOME/.local/share}/fonts/RajdhaniMono"
cp fonts/ttf/*.ttf "${XDG_DATA_HOME:-$HOME/.local/share}/fonts/RajdhaniMono/"
fc-cache -f
```

若已经安装 v0.1，请覆盖更新并重启终端或编辑器，以便加载新版字体。

[`docs/preview.html`](docs/preview.html) 是完全离线的试字页，嵌入了五个字重，可以调整字号、背景和文字。下载到本地后用浏览器打开即可，无需安装字体。GitHub 文件页面显示 HTML 源码。

网页字体位于 [`fonts/woff2/`](fonts/woff2)。

## 字重与字符覆盖

| 字重 | 数值 |
| --- | ---: |
| Light | 300 |
| Regular | 400 |
| Medium | 500 |
| SemiBold | 600 |
| Bold | 700 |

每个字重覆盖 **854 个编码字符**，包含 ASCII、原字体的拉丁扩展、标点、部分数学符号、箭头、完整线框和方块字符，以及八个 Powerline 符号。

- 所有可打印编码字符的字宽为 **520/1000 em**；组合重音与零宽控制符不额外占格。
- `I` 有上下横杠，`l` 有顶部标识和底脚，`1` 有底脚，`0` 有中心点。
- 调整 `m` 和 `M` 的字腔时保留直立笔画粗细。
- 下划线延伸至字格两端，粗细随字重调整。
- 保留代码字符的一字一格排版，不包含字距调整或编程连字。
- 包含 14 个组合重音及其定位，补齐了罗马尼亚字符 `Ț/ț`。

## v0.2 的调整

字格从 **560 缩到 520**，约减少 **7.1%**。最小两侧留白从 40 调到 20，最大字形宽度保持 480，因此字母轮廓尺寸保留。

首版将 `_` 固定为 36 单位厚。v0.2 改为匹配各字重的水平笔画：Light / Regular / Medium / SemiBold / Bold 分别为 **30 / 44 / 61 / 80 / 102** 单位，并同步调整文本下划线的字体元数据。

![v0.1 与 v0.2 对比](docs/images/comparison.png)

下载 [`docs/comparison.html`](docs/comparison.html) 后，可以在同字号、同字重下交互比较 v0.1 与 v0.2。

## 当前范围

这是可试用的早期版本，已经在 Linux 字体工具、FreeType 和 HarfBuzz 中验证，尚未在 Windows、macOS 或具体终端应用中完成实测。

- 暂不包含中文、天城文、完整希腊/西里尔文字、斜体或变量字体。
- Powerline 符号不等于完整 Nerd Font 图标集；缺字依赖应用的字体回退。
- 组合重音支持常见单层顶部和底部重音，多层堆叠重音尚需精修。
- Light 在小字号下较淡；`W/w` 和非常宽的符号仍可继续手工调整。
- 线框按默认字行度量连接；增加终端行间距会在垂直连接处留下间隙。

## 从源码构建

构建输入已经随仓库保存，不需要在构建时下载上游字体。所有来源文件都有固定 Git 提交和 SHA-256 校验值，见 [`sources/manifest.json`](sources/manifest.json)。

需要 Python 3.10+，推荐 **Python 3.12**：

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_font.py
.venv/bin/python scripts/make_preview.py
```

Windows 请将 `.venv/bin/python` 换成 `.venv\Scripts\python.exe`。

构建后的 TTF 和 WOFF2 位于 `fonts/`，未拟合的中间文件位于被 Git 忽略的 `build/`，构建概要位于 `reports/`。`make_preview.py` 更新当前字体的离线试字页和样张；历史版本对比文件单独保留。

## 验证与打包

```sh
.venv/bin/python scripts/validate_font.py
.venv/bin/python scripts/check_rebuild.py
.venv/bin/python scripts/package_release.py
```

验证覆盖字符度量、实际文字排版、重音定位、笔画保持、格边连接、WOFF2 解码一致性，以及全部字符在 12 / 16 / 20 / 32 px 下的渲染。

安装 Fontconfig 和 OpenType Sanitizer 后，可以执行完整的外部工具检查：

```sh
.venv/bin/python scripts/validate_font.py --require-fontconfig --ots ots-sanitize
```

`fc-scan` 不可用时，默认跳过 Fontconfig 检查，并在报告中记为 `null`；其他检查继续执行。`--require-fontconfig` 会将缺少该工具视为失败。

[`GitHub Actions`](.github/workflows/fonts.yml) 会在 push 和 pull request 时运行验证、逐字节重建比较，并生成可下载的字体包。打包结果位于 `dist/`，包含字体、来源、构建脚本、文档、完整许可和校验值。

## 发布到 GitHub

将这个目录提交并推送到自己的仓库即可。需要创建字体发行版时，运行打包命令，将 `dist/RajdhaniMono-v0.2.zip` 和对应 `.sha256` 文件添加到 GitHub Release，版本标签可使用 `v0.2`。

该仓库没有配置自动发布 Release 或网站的流程。

## 开源来源与许可

拉丁字形来自 Indian Type Foundry 的 Rajdhani，采用 [Google Fonts 官方发行](https://github.com/google/fonts/tree/main/ofl/rajdhani)的五个稳定 TTF 作为输入。补充终端绘图、箭头和数学符号来自 [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono)，未引入其拉丁字母或编程连字。

| 输入 | 固定提交 |
| --- | --- |
| Google Fonts / Rajdhani | `8772f86137e17678cbd3584ca9a3c9486c3e7e50` |
| JetBrains Mono | `19371302b95d218af43299bce79ddbddd0bc364d` |

原始版权声明和许可保存在各自的 `sources/` 目录中。衍生字体和构建配方按 [SIL OFL 1.1](LICENSE) 分发，完整署名见 [NOTICE.txt](NOTICE.txt)。本项目与 Indian Type Foundry 或 JetBrains 没有官方关联，署名用于注明来源。

问题反馈和贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)，版本记录见 [CHANGELOG.md](CHANGELOG.md)。
