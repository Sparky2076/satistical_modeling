# satistical_modeling

统计建模大赛专用仓库（与 GitHub 仓库同名：`Sparky2076/satistical_modeling`）。

- 思路概要见根目录 [`zero2one.pdf`](./zero2one.pdf)。
- **本地路径：`D:\GitHub_Code\satistical_modeling`**

## 目录规划（可后续补充）

| 路径 | 说明 |
|------|------|
| `data/` | 原始与清洗后数据（大文件建议 Git LFS 或不上传） |
| `notebooks/` | 探索性分析与试算 |
| `src/` | 可复用脚本与模型代码 |
| `docs/` | 说明、图表、论文 Markdown/LaTeX |

## 远程仓库

```text
https://github.com/Sparky2076/satistical_modeling.git
```

克隆：

```powershell
cd D:\GitHub_Code
git clone https://github.com/Sparky2076/satistical_modeling.git
```

已在本地配置 `origin`，日常推送用 **PowerShell**：

```powershell
cd D:\GitHub_Code\satistical_modeling
.\push.ps1 -Message "你的提交说明"
```

不写 `-Message` 时默认提交信息为 `update`：

```powershell
.\push.ps1
```

或手写：

```powershell
cd D:\GitHub_Code\satistical_modeling
git add .
git commit -m "你的说明"
git push origin main
```

若提示「无法加载，因为在此系统上禁止运行脚本」，可先执行（当前用户即可）：

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## 当前数据状态（2026-04-15）

已在本地仓库生成并保存：

- `data/processed/occupation_exposure.csv`
- `data/processed/occupation_code_mapping.csv`
- `data/raw/jobs/jobs_micro_raw.csv`（最近一年招聘快照）

对应脚本：

- `src/build_occupation_exposure.py`
- `src/build_occupation_code_mapping.py`
- `src/fetch_jobs_micro_raw.py`
- `src/download_anthropic_economic_index.py`

说明：**CFPS（你消息中写作 CPFS）个体面板数据仍在申请中，尚未并入仓库。**
