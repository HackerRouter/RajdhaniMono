# Contributing

感谢测试和改进 Rajdhani Mono。当前重点是小字号可读性、窄字母和符号的轮廓质量，以及不同终端中的显示效果。

## 反馈显示问题

请在 issue 中提供字体版本、字重、字号、操作系统、终端或编辑器名称，以及可以复制的示例文字。若涉及缺字，请尽量注明 Unicode 编码；截图可以帮助比较实际显示效果。

## 修改字体

1. 创建分支，安装 `requirements.txt` 中的依赖。
2. 修改 `scripts/build_font.py`；若新增上游素材，同时记录来源、许可、固定版本和校验值。
3. 执行字体构建、验证与逐字节重建检查。
4. 更新样张和相关文档，在 PR 中说明字形或度量的具体变化。

```sh
python scripts/build_font.py
python scripts/validate_font.py
python scripts/check_rebuild.py
python scripts/make_preview.py
```

这些命令应在已激活依赖环境后执行。CI 还会使用 Fontconfig 和 OpenType Sanitizer 检查最终文件。

请提交对应的 TTF、WOFF2 和验证报告。字体构建配方与新增轮廓按本项目的 SIL OFL 1.1 许可分发，并保留所有上游素材的完整署名与许可。

## 当前设计约束

- 可打印单格字符使用一致的 advance；组合重音和零宽控制字符保持零宽。
- 新符号应与现有字重匹配，并在小字号下检查。
- 拉丁文字之外的脚本扩展，需要先设计其完整排版与回退行为。
- 不以改变代码列对齐的连字或字距调整掩盖字形问题。

## English

Report the font version, weight, size, platform, application, and a reproducible text sample. Unicode code points and screenshots are useful for missing-glyph or rendering reports.

Changes should include the build recipe, generated fonts, refreshed reports, and relevant specimens. Run the build, validation, reproducibility, and preview commands before submitting a PR. Document the provenance and license of any added source material, and preserve upstream notices.
