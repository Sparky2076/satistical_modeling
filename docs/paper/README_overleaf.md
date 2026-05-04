# Overleaf 上使用本论文工程

## 上传

1. 将 `**docs/paper/**` 整夹打包为 zip（保留子目录 `sections/`、`figures/`、`tools/` 可选可不传）。
2. 在 Overleaf 新建项目 → **Upload project**。
3. **Menu → Compiler** 设为 **XeLaTeX**（必须：中文与 `ctex`）。
4. **Menu → Main document** 设为 `**main.tex`**。

## 字体

模板使用 `ctex` 默认中文配置。若编译报缺字库，可在 `preamble.tex` 的 `\documentclass` 增加 `fontset` 选项，例如：

```latex
\documentclass[UTF8,a4paper,zihao=-4,fontset=fandol]{ctexart}
```

也可尝试 `fontset=windows`（取决于 Overleaf 环境是否含相应字体）。详见 [Overleaf 中文与 XeLaTeX 文档](https://www.overleaf.com/learn/latex/Chinese)。

## 本地编译（可选）

已安装 TeX Live / MiKTeX 时，在 `docs/paper/` 下：

```bash
xelatex main.tex
xelatex main.tex
```

第二遍用于更新目录与交叉引用。

**仅编译「识别 / 置换检验」附录（含公式）**：在同一目录执行 `xelatex identification_placebo_standalone.tex`（主文件为 [`identification_placebo_standalone.tex`](identification_placebo_standalone.tex)，内容来自 [`sections/identification_placebo_writeup.tex`](sections/identification_placebo_writeup.tex)；与主文 `main.tex` 中的附录 D 同源）。

## 常见报错

- **找不到图**：确认 `figures/` 内已含 `fig01`…`fig04` 等 png（可从仓库 `output/figures/` 复制，见 `sections/empirical_figures_inline.tex`）。
- **数学环境错误**：正文大部由 `draft.md` 自动生成，复杂公式若报错，可在对应 `sections/body_autogen.tex` 段落手工改为 `equation` / `aligned`。
- `**underscore` 与路径**：`preamble.tex` 中 `\usepackage[strings]{underscore}` 便于正文中的 `task_id` 等下划线；若与某宏包冲突可临时注释并手工转义 `_`。

---

## 终稿回到 Word（赛后排版）

LaTeX PDF 与大赛 Word 模板通常无法像素级一致，终稿应以《论文要素及格式要求》**docx 母版**为准。

**方式 A — Pandoc（自动化程度有限）**

若本机已安装 [Pandoc](https://pandoc.org/)，可准备一份按格式要求排好样式空壳的 `reference.docx`，再尝试：

```bash
pandoc main.tex -o paper_from_tex.docx --reference-doc=reference.docx
```

复杂公式、分栏、域与自动目录往往仍需在 Word 中手工调整。

**方式 B — 手工对齐（大赛常用）**

在 Word 母版中按节对照 PDF / 分屏粘贴修订；图表用可编辑对象或高分辨率插入，公式用 Word 自带编辑器或 MathType 重录。

**方式 C — PDF 作参照**

仅将 PDF 作为内容参照，**不**建议用「整页 PDF 图片」代替正文矢量文字，以免影响查重与编辑。