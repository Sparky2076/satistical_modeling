# B.2 API 价目：官方链接与 CSV 正文（2026-05-02 核对）

将下方 **CSV 代码块** 全选复制，覆盖保存为 `[../api_price_schedule.csv](../api_price_schedule.csv)` 即完成 B.2 表体更新。

**人民币→美元**：阿里云、百度两行按文内价格换算，`fx_cny_per_usd=7.20`（见各 `notes`）。智谱「元/百万 Tokens」按 **输入与输出同单价** 拆入两列（若控制台实际分项不同请改正）。

## 各厂商一级文档入口（逐项打开核对）


| 厂商            | 建议打开的定价/计费页                                                                                                           |
| ------------- | --------------------------------------------------------------------------------------------------------------------- |
| OpenAI        | [https://platform.openai.com/docs/pricing](https://platform.openai.com/docs/pricing)                                  |
| DeepSeek      | [https://api-docs.deepseek.com/quick_start/pricing/](https://api-docs.deepseek.com/quick_start/pricing/)              |
| Anthropic     | [https://platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing)  |
| Google Gemini | [https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)                        |
| 阿里云百炼         | 控制台与帮助中心「模型计费」为准；下列为汇总参考 [https://developer.aliyun.com/article/1718400](https://developer.aliyun.com/article/1718400) |
| 百度千帆          | [https://ai.baidu.com/ai-doc/WENXINWORKSHOP/Hm88dcygk](https://ai.baidu.com/ai-doc/WENXINWORKSHOP/Hm88dcygk)          |
| 智谱 BigModel   | [https://docs.bigmodel.cn/cn/guide/models/text/glm-4](https://docs.bigmodel.cn/cn/guide/models/text/glm-4)            |


## `api_price_schedule.csv` 全文（与仓库列名一致）

```csv
provider,model_id,pricing_tier,input_price_per_1m_usd,cached_input_price_per_1m_usd,output_price_per_1m_usd,batch_discount_note,context_window_tokens,price_collected_date,source_url,notes
DeepSeek,deepseek-v4-flash,standard,0.14,0.0028,0.28,,1000000,2026-05-02,https://api-docs.deepseek.com/quick_start/pricing/,Official table; deepseek-chat alias non-thinking
DeepSeek,deepseek-v4-pro,standard,1.74,0.0145,3.48,75pct_discount_until_2026-05-31_per_official_page,1000000,2026-05-02,https://api-docs.deepseek.com/quick_start/pricing/,List prices; promo discount dates on same page
OpenAI,gpt-5.4-nano,standard,0.2,0.02,1.25,Batch_tier_rows_on_same_page,272000,2026-05-02,https://platform.openai.com/docs/pricing,Cheap baseline from flagship Standard table
OpenAI,gpt-4o-mini,standard,0.15,0.075,0.6,Batch_tier_rows_on_same_page,128000,2026-05-02,https://platform.openai.com/docs/pricing,
OpenAI,gpt-4o,standard,2.5,1.25,10,Batch_tier_rows_on_same_page,128000,2026-05-02,https://platform.openai.com/docs/pricing,
OpenAI,gpt-5.4,standard,2.5,0.25,15,Batch_tier_rows_on_same_page,272000,2026-05-02,https://platform.openai.com/docs/pricing,Frontier general; context cap from pricing row text
OpenAI,o4-mini,standard,1.1,0.275,4.4,Batch_tier_rows_on_same_page,200000,2026-05-02,https://platform.openai.com/docs/pricing,Reasoning-family budget
Anthropic,claude-haiku-4-5,standard,1.0,0.10,5.0,Batch_and_1h_cache_write_rates_differ_see_source,1000000,2026-05-02,https://platform.claude.com/docs/en/about-claude/pricing,cached_input_uses_Cache_Hits_and_Refreshes_column_0.10_MTok
Anthropic,claude-sonnet-4-6,standard,3.0,0.30,15.0,Batch_and_cache_tiers_on_same_page,1000000,2026-05-02,https://platform.claude.com/docs/en/about-claude/pricing,1M_context_at_standard_pricing_per_doc
Anthropic,claude-opus-4-7,standard,5.0,0.50,25.0,Batch_and_cache_tiers_on_same_page,1000000,2026-05-02,https://platform.claude.com/docs/en/about-claude/pricing,Top_tier_frontier_option
Google,gemini-2.5-flash-lite,standard,0.10,0.01,0.40,,1000000,2026-05-02,https://ai.google.dev/gemini-api/docs/pricing,Paid_Standard_text_image_video_input_row
Google,gemini-2.5-flash,standard,0.30,0.03,2.50,,1000000,2026-05-02,https://ai.google.dev/gemini-api/docs/pricing,Output_includes_thinking_tokens_per_Google_doc
Alibaba,qwen-plus,standard,0.11111111,0,0.27777778,,128000,2026-05-02,https://developer.aliyun.com/article/1718400,CNY_from_article_0.0008_and_0.002_per_1k_tokens_fx_7.20_to_USD_per_1M;verify_Model_Studio_console
Alibaba,qwen-turbo,standard,0.04166667,0,0.08333333,,128000,2026-05-02,https://developer.aliyun.com/article/1718400,CNY_0.0003_and_0.0006_per_1k_tokens_fx_7.20;verify_console
Baidu,ERNIE-4.0-8K,standard,0.55555556,0,2.22222222,,8192,2026-05-02,https://ai.baidu.com/ai-doc/WENXINWORKSHOP/Hm88dcygk,Post_2025-03-16_list_0.004_and_0.016_CNY_per_1k_tokens_fx_7.20
Baidu,ERNIE-4.0-Turbo-8K,standard,0.41666667,0.16666667,1.25,,8192,2026-05-02,https://ai.baidu.com/ai-doc/WENXINWORKSHOP/Hm88dcygk,List_0.003_and_0.009_CNY_per_1k_out;cache_0.0012_CNY_per_1k_tokens_fx_7.20
Zhipu,glm-4-air-250414,standard,0.06944444,0,0.06944444,,128000,2026-05-02,https://docs.bigmodel.cn/cn/guide/models/text/glm-4,Official_0.5_CNY_per_1M_tokens_applied_to_both_in_and_out_fx_7.20_if_billing_splits_verify_console
Zhipu,glm-4-plus,standard,0.69444444,0,0.69444444,,128000,2026-05-02,https://docs.bigmodel.cn/cn/guide/models/text/glm-4,Official_5_CNY_per_1M_tokens_applied_to_both_in_and_out_fx_7.20_if_billing_splits_verify_console
```

## B.2 完成自检

- todo 列出的 7 类厂商均有对应 `source_url` 行（阿里行为汇总参考 + 控制台待核）。
- 含低价国产、中端、前沿、推理（`o4-mini` / `ERNIE-4.0-Turbo` 等）组合，行数 > 10。
- `price_collected_date` 与访问日一致；调价后请重抓并改日期。

---

## 末次人工核对外链（占位）

- **本文档标题日期**：2026-05-02。  
- **下次复查**：打开上表各厂商链接，确认仍有效后，更新本行日期、`api_price_schedule.csv` 中 `price_collected_date` 与 [`reproducibility_baseline.md`](reproducibility_baseline.md) 中价目小节。

