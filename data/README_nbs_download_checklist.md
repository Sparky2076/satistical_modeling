# 国家统计局人工下载清单

网站：`https://data.stats.gov.cn/`（无需登录可搜索/预览）

## 操作流程（每张表都按此流程）

1. 打开数据查询页，输入“检索关键词”。
2. 选择“年度数据”，地区维度选“31省（不含港澳台）”。
3. 年份范围按下表要求导出。
4. 导出 CSV 后放入仓库指定路径。
5. 运行本脚本校验：`py -3.13 src/nbs_download_checklist.py --validate-only`

## 需要下载的表

### 1) Bartik base: province manufacturing employment share in 2010
- 文件路径：`data/raw/share_p2010.csv`
- 年份范围：`2010-2010`
- 预期列：`provcd, share_p2010`
- 检索关键词：`分地区 | 按行业就业人员 | 制造业 | 城镇单位就业人员 | 2010`
- 备注：需要31省统一口径。share_p2010 建议在 [0,1]。

### 2) Province-year controls for regressions
- 文件路径：`data/raw/province_controls_raw.csv`
- 年份范围：`2010-2020`
- 预期列：`provcd, year, gdp, population, urban_rate, unemployment_rate, mfg_share`
- 检索关键词：`地区生产总值 | 常住人口 | 城镇化率 | 失业率 | 制造业占比 | 分地区 | 2010-2020`
- 备注：控制变量建议年频并覆盖全部省份。
