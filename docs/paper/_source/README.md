# `_source/`：Word 抽取结果

本目录由仓库根目录两份 **docx** 经 `tools/extract_docx.py` 生成（stdlib `zipfile` + `xml.etree`，不依赖 Pandoc）：

- `format_outline.md`：来自较小的《论文要素及格式要求》类文件。
- `draft.md`：来自较大的统模初稿 docx。

## 重新生成

在仓库根目录执行：

```bash
python docs/paper/tools/extract_docx.py
python docs/paper/tools/draft_md_to_body_tex.py
```

第二行脚本会更新 `sections/body_autogen.tex`（正文至参考文献前）与 `sections/body_backmatter.tex`（参考文献、附录、致谢）。

## Git 策略

若初稿含隐私或体积过大，可将 `draft.md` 列入 `.gitignore`，仅本地保留；`main.tex` 仍可依赖已提交的 `.tex` 章节。
