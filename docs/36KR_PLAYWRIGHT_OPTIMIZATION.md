# 36氪 Playwright 优化记录（历史）

> 本文档为历史优化总结，保留反验证码与诊断思路。当前运行入口已迁移到 Skills 模式。

## 当前入口

- `.agents/skills/financial-news-video-workflow/scripts/crawl_news.py`
- 36氪逻辑在该脚本内由对应 Source 实现
- 推荐通过 Skill 触发：`/financial-video`

手动调试示例：

```bash
python .agents/skills/financial-news-video-workflow/scripts/crawl_news.py --days 3 --sources 36kr
```

---

## 历史内容可复用点

1. 验证码诊断与截图留痕
2. 人类滚动与轨迹模拟
3. 失败回退策略
4. Stealth 与上下文持久化

---

## 迁移注意

历史文档中的以下名称在当前仓库中不再是主入口：

- `financial_news_workflow_crawl4ai.py`
- `crawl_36kr_realtime.py`

如需继续调参，请直接编辑 `skills` 下脚本并通过工作流验证。
