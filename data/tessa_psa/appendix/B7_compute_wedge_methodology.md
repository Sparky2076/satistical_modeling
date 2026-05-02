# B7 可选算力楔：指数定义与来源

与 [`compute_service_wedge_optional.csv`](../compute_service_wedge_optional.csv) 对齐。采集日期：**2026-05-02**。

## 1. 下游 `downstream_api_price_index`（API 价格指数）

| 项目 | 约定 |
|------|------|
| 锚定产品 | OpenAI **GPT-4o 系列**当时可用的**旗舰**文本 API 快照（与 `api_price_schedule.csv` 中 gpt-4o 口径一致） |
| 价格变量 \(P_t\) | 官方标价 **输出（output）USD / 1M tokens**，标准计费（非 Batch 特价） |
| 基期与公式 | 令 **\(P_{\mathrm{ref}} = 10\)** USD/1M（对应 **gpt-4o-2024-08-06** 及后续同价快照的清单价）。**指数 = 100 × \(P_t / P_{\mathrm{ref}}\)**。数值上升表示 API 输出更贵。 |

### 1.1 关键时点与来源

| 时期（季度末） | \(P_t\)（USD/M output） | 依据 |
|----------------|-------------------------|------|
| 2024-06-30 及更早（gpt-4o-2024-05-13） | 15 | OpenAI Platform 定价表列 `gpt-4o-2024-05-13`；模型发布叙事见 [Hello GPT-4o](https://openai.com/index/hello-gpt-4o/)（2024-05-13） |
| 2024-09-30 起 | 10 | 同上定价表 `gpt-4o-2024-08-06` / 默认 `gpt-4o` 文本输出；发布节点见 [API Changelog](https://developers.openai.com/api/docs/changelog)（August 2024 / gpt-4o-2024-08-06） |

当前价目总入口（会随官方更新变化，摘录以采集日为准）：

- https://platform.openai.com/docs/pricing  
- https://developers.openai.com/api/docs/models/gpt-4o  

## 2. 上游 `upstream_gpu_cloud_proxy_index`（云 GPU 清单价代理）

| 项目 | 约定 |
|------|------|
| 锚定资源 | **Amazon EC2 `p4d.24xlarge`**，区域 **US East (N. Virginia) (`us-east-1`)**，**Linux**，**On-Demand**（非 Spot） |
| 价格变量 \(H_t\) | 公开目录 **美元/实例小时**（8×A100 40GB 整机价，作算力成本代理） |
| 基期与公式 | 令 **\(H_{\mathrm{ref}} = 21.96\)** USD/h（**2025-06-01** AWS 官宣 GPU 实例降价后的目录价水平，与第三方价目镜像一致）。**指数 = 100 × \(H_t / H_{\mathrm{ref}}\)**。 |
| 降价前隐含价 | AWS 称 P4d On-Demand 相对 **2025-05-31** 基线最高约 **33%** 降幅，故取 **\(H_{\mathrm{pre}} = H_{\mathrm{ref}}/(1-0.33)=21.96/0.67 \approx 32.78\)** USD/h 作为 2025-06-01 前的代理目录价（反推值，四舍五入两位小数）。 |

### 2.1 官方依据（降价事件）

- [What’s New — Pricing and usage model updates for EC2 NVIDIA GPU instances](https://aws.amazon.com/about-aws/whats-new/2025/06/pricing-usage-model-ec2-instances-nvidia-gpus/)（生效自 2025-06-01 等）  
- [AWS News Blog — Up to 45% price reduction for EC2 NVIDIA GPU-accelerated instances](https://aws.amazon.com/blogs/aws/announcing-up-to-45-price-reduction-for-amazon-ec2-nvidia-gpu-accelerated-instances/)（含 P4d **33%** On-Demand 降幅表）  

### 2.2 现价二次核对（非官方，仅便读）

- [instances.vantage.sh — p4d.24xlarge us-east-1](https://instances.vantage.sh/aws/ec2/p4d.24xlarge?region=us-east-1)（镜像 AWS 目录价，约 **21.958** USD/h，与 21.96 一致量级）  

## 3. `provider` 与主键

- 本表采用 **`provider=composite_quarterly`**：每行同时给出下游与上游指数，主键为 **`date` + `provider`**。  

## 4. 局限

- 未使用 Internet Archive 对历史价目页做逐日爬取；**2025-06-01 前** GPU 价采用官方降幅反推的**常数代理**，非 AWS 逐日价目表逐字抄录。  
- 下游未覆盖 GPT-4o 发布前季度（该时点无同口径旗舰 API 价）。  
- 本模块为 **可选扩展**，不参与当前仓库内主估计代码路径。  
