# 钛媒体抓取开发备注（历史）

> 本文档保留开发过程记录。当前仓库已迁移到 Skills 模式，以下内容请结合“当前入口”使用。

## 当前入口（请优先使用）

- 主入口脚本：`.agents/skills/financial-news-video-workflow/scripts/crawl_news.py`
- 钛媒体实现位置：`SourceTmtpost`
- 调用方式：由 `financial-news-video-workflow` Skill 自动触发

手动调试示例：

```bash
python .agents/skills/financial-news-video-workflow/scripts/crawl_news.py --days 5 --sources tmtpost
```

---

## 历史说明

本文件原始内容描述了独立 `crawl_tmtpost_realtime.py` 的开发路径（含 `--target` 与 `--method` 参数）。
在当前仓库版本中，这些参数和入口不再作为主路径。

保留的技术结论（仍有参考价值）：

1. 视频过滤应双重校验：`item_type` + URL 规则
2. 时间过滤应采用“整页超时再停止”策略
3. API 优先、浏览器回退可提升稳定性

---

## 当前实现映射

- 历史“API 模式” -> 当前 `SourceTmtpost._fetch_by_api()`
- 历史“Playwright 模式” -> 当前 `SourceTmtpost._fetch_by_playwright()`
- 历史“独立输出 news_output/*.json” -> 当前统一输出到 `output/pipeline_output_*/crawl_news_result/news_raw.json`

---

## 建议

如果要继续优化钛媒体抓取，请直接修改：

- `.agents/skills/financial-news-video-workflow/scripts/crawl_news.py`
- `.agents/skills/financial-news-video-workflow/SKILL.md`

并通过 Skill 工作流回归验证。
