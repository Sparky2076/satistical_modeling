# B4 任务库来源索引（工作稿）

访问整理日期：**2026-05-02**。

## 1. 政务 / 部委 / 公共服务栏目（`task_source`）

`task_bank.csv` 中 `ps-*` 行的 `task_source` 轮取自 [`src/tepsa_task_bank_portal_data.py`](../../../src/tepsa_task_bank_portal_data.py) 内 `PUBLIC_SERVICE_URLS`（国务院公报、国家医保局栏目、生态环境部转载、民政部、人社部入口、发改委、财政部、卫健委、司法部、公安部、中央纪委国家监委等门户或政策栏目）。**同一 URL 可对应多条不同 `task_text`**，便于在固定权威入口下覆盖多类办事咨询问题。

## 2. 企业服务 / 监管 / 产业政策（`es-*`）

见同文件 `ENTERPRISE_URLS`：国家税务总局、市场监管总局、发改委、财政部、生态环境部、海关总署、金融监管总局、证监会、外汇局、工信部、国家统计局、中国政府网「最新政策」等。

## 3. 安全生产与标准（`mfg-*`）

见 `MANUFACTURING_URLS`：应急管理部、中国安全生产网、市场监管国家标准平台、国标公开系统、工信部等。

## 4. 教育政策（`edu-*`）

见 `EDUCATION_URLS`：教育部政府信息公开与新闻发布栏目、中国政府网、国家卫健委门户等。

## 5. 技术文档（`code-*`）

见 `CODE_URLS`：**Python 3 官方文档**（`docs.python.org`）章节链接。

## 6. 基准锚点（`ceval-*` / `cmmlu-*`）

- **C-Eval**：行内 `task_source` 标注 `HuggingFace ceval/ceval-exam` 的 config 与 `val` 行号；完整可复制快照见同目录 [`b4_benchmark_snapshot.json`](b4_benchmark_snapshot.json)，由 [`src/tepsa_task_bank_benchmark_gen.py`](../../../src/tepsa_task_bank_benchmark_gen.py) 生成。许可证：**CC BY-NC-SA 4.0**（见 C-Eval 官方仓库说明）；论文引用见 Huang et al., NeurIPS 2023。
- **CMMLU**：`task_source` 标注 `GitHub haonan-li/CMMLU` 的 `data/dev/*.csv`；快照同源生成。许可证：**CC BY-NC-SA 4.0**。

## 7. 再生与更新

```text
# 仅 stdlib：生成基准快照 JSON（网络不通时仍可用已提交快照）
python src/tepsa_task_bank_benchmark_gen.py

# 合并门户任务 + 快照，写出 task_bank.csv
python src/tepsa_task_bank_build.py
```

若需刷新门户 URL，请直接编辑 `tepsa_task_bank_portal_data.py` 中各 `*_URLS` 列表并重新运行 `tepsa_task_bank_build.py`。
