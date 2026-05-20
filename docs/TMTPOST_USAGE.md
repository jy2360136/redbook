# 钛媒体抓取说明（当前版本）

## 重要变更

本仓库当前不使用独立 `crawl_tmtpost_realtime.py`。

钛媒体抓取已并入：
- `.agents/skills/financial-news-video-workflow/scripts/crawl_news.py`
- 内部实现：`SourceTmtpost`（API 优先，Playwright 回退）

---

## 推荐调用方式（Skills）

直接触发：
- `/financial-video`
- `金融新闻视频`

由 AI 决定是否执行抓取脚本。

---

## 手动调试方式

### 仅抓钛媒体

```bash
python .agents/skills/financial-news-video-workflow/scripts/crawl_news.py --days 5 --sources tmtpost
```

### 抓四个核心源

```bash
python .agents/skills/financial-news-video-workflow/scripts/crawl_news.py --days 5 --sources huxiu,36kr,tmtpost,jiemian
```

### 指定输出目录

```bash
python .agents/skills/financial-news-video-workflow/scripts/crawl_news.py --days 5 --sources tmtpost --output output/pipeline_output_debug/crawl_news_result
```

---

## 参数说明（以 `crawl_news.py` 为准）

- `--days`：近 N 天（默认 3）
- `--sources`：`huxiu,36kr,tmtpost,jiemian` 或 `all`
- `--output`：输出目录
- `--filter-companies`：是否按公司关键词过滤

---

## 输出格式

产物默认位于：

```text
output/pipeline_output_YYYYMMDD_HHMMSS/crawl_news_result/news_raw.json
```

结构示例：

```json
{
  "fetch_time": "2026-04-05T23:17:22",
  "total": 1866,
  "by_source": {
    "虎嗅网": 1182,
    "36 氪": 208,
    "钛媒体": 449,
    "界面新闻": 27
  },
  "news": [
    {
      "source": "钛媒体",
      "title": "标题——摘要",
      "link": "https://www.tmtpost.com/...",
      "published": "2026-03-30 07:20:00"
    }
  ]
}
```

---

## 说明

历史文档中出现的 `--target`、`--method api/playwright/both` 是旧独立脚本参数，不适用于当前仓库版本。
