# 钛媒体爬虫使用说明

## 快速开始

### 基本用法

```bash
# 获取最近 5 天的 200 条文字新闻（推荐）
python crawl_tmtpost_realtime.py --days 5 --target 200
```

### 参数说明

| 参数       | 类型 | 默认值 | 说明                              |
| ---------- | ---- | ------ | --------------------------------- |
| `--days`   | int  | 5      | 获取最近几天的文章                |
| `--target` | int  | 200    | 目标抓取数量                      |
| `--method` | str  | api    | 抓取方式：api / playwright / both |

### 三种抓取模式

#### 1. API 模式（默认，推荐）

```bash
python crawl_tmtpost_realtime.py --days 5 --target 200 --method api
```

**优点**：

- ✅ 速度快：直接调用 API，无需启动浏览器
- ✅ 成功率高：不受网页反爬影响
- ✅ 数据准：官方结构化数据
- ✅ 过滤好：通过 `item_type` 精确过滤视频

**适用场景**：日常使用、批量获取

#### 2. Playwright 模式

```bash
python crawl_tmtpost_realtime.py --days 5 --target 200 --method playwright
```

**优点**：

- ✅ 模拟真实用户行为
- ✅ 可获取页面显示的所有内容

**适用场景**：API 失效时备用方案

#### 3. 双模式

```bash
python crawl_tmtpost_realtime.py --days 5 --target 200 --method both
```

**执行流程**：

1. 先用 API 抓取
2. 如果不够目标数量，再用 Playwright 补充
3. 自动去重

**适用场景**：需要大量数据时

## 输出结果

### 文件位置

```
news_output/
└── news_output_20260330_082734.json
```

**命名规则**：`news_output_YYYYMMDD_HHMMSS.json`

### 文件格式

```json
{
  "fetch_time": "2026-03-30T08:27:41",
  "days": 5,
  "target": 200,
  "method": "api",
  "total": 206,
  "by_source": {
    "钛媒体": 206
  },
  "news": [
    {
      "source": "钛媒体",
      "title": "文章标题",
      "link": "https://www.tmtpost.com/7933771.html",
      "published": "2026-03-30 07:20:00",
      "author": "作者名",
      "summary": "文章摘要...",
      "number_of_reads": "20123",
      "number_of_upvotes": 3
    }
  ]
}
```

### 字段说明

| 字段              | 说明     | 示例                                 |
| ----------------- | -------- | ------------------------------------ |
| source            | 新闻来源 | 钛媒体                               |
| title             | 文章标题 | 【钛晨报】北京启动 L2...             |
| link              | 原文链接 | https://www.tmtpost.com/7933771.html |
| published         | 发布时间 | 2026-03-30 07:20:00                  |
| author            | 作者     | 钛媒体官方账号                       |
| summary           | 摘要     | 马斯克旗下 AI 公司...                |
| number_of_reads   | 阅读量   | 20123                                |
| number_of_upvotes | 点赞数   | 3                                    |

## 核心功能

### 1. 视频新闻过滤 ✅

**双重过滤机制**：

1. **API 级别**：只保留 `item_type == "post"` 的文章
   - 自动排除 `item_type == "video_article"` 的视频

2. **URL 级别**：检查链接是否包含 `/video/`
   - 过滤格式：`https://www.tmtpost.com/video/7933501.html`

**测试结果**：

```
✅ 文字新闻：206 条 (100%)
❌ 视频新闻：0 条 (0%)
🎉 视频过滤成功！
```

### 2. 智能时间筛选 ⏰

**支持的日期格式**：

- 相对时间："X 小时前"、"X 天前"、"约 X 小时以前"
- 星期："上周"、"星期 X"
- 特殊："刚刚"、"今天"、"昨天"、"前天"
- 绝对日期："2026-03-30"、"2026.3.30"

**智能停止逻辑**：

- 不是遇到一篇超时文章就停止
- 而是当一页所有文章都超时时才停止
- 可以获取更多符合时间范围的文章

### 3. 目标数量控制 🎯

- 达到 `--target` 数量后自动停止
- 避免无限制抓取
- 节省时间和资源

## 技术细节

### API 端点

```
GET https://api.tmtpost.com/v1/lists/new
```

### 关键参数

```python
params = {
    "limit": "20",          # 每页 20 条
    "offset": "0",          # 起始偏移量
    "subtype": "post;atlas;video_article;fm_audios;",
}
```

### 请求头生成

基于真实抓包数据，包含：

- `app-key`: "2015042403"
- `app-secret`: "F3x47g39Wc4M96nwA28T"
- `timestamp`: 毫秒级时间戳
- `token`: Base64 编码的时间戳
- `authorization`: MD5 签名

### 分页逻辑

```python
offset = 0
limit = 20
max_pages = 50  # 最多 1000 条

for page in range(max_pages):
    params["offset"] = str(offset)
    response = requests.get(api_url, params=params)

    if len(all_news) >= target:
        break  # 达到目标

    offset += limit
```

## 常见问题

### Q1: 为什么有时候抓取不到 200 条？

**可能原因**：

1. 时间范围太短（如只获取 1 天内）
2. 钛媒体网站本身就没有那么多新文章
3. API 请求被限流

**解决方案**：

- 增加 `--days` 参数，如改为 7 天或 10 天
- 降低 `--target` 目标数量
- 使用 `--method both` 双模式

### Q2: 如何验证视频是否被过滤？

运行测试脚本：

```bash
python test_tmtpost.py
```

会显示：

- 文字新闻数量
- 视频新闻数量
- 前 10 条的链接类型

### Q3: API 请求失败怎么办？

**错误示例**：

```
❌ 第 1 页请求失败：403
```

**解决方案**：

1. 切换到 Playwright 模式：`--method playwright`
2. 检查网络连接
3. 更新请求头（可能需要重新抓包）

### Q4: 输出的 JSON 文件在哪里？

统一在 `news_output/` 目录下：

```
c:\Users\Administrator\Desktop\redbook\news_output\
├── news_output_20260330_082734.json
└── news_output_20260330_093015.json
```

## 依赖安装

```bash
# 必需
pip install requests playwright playwright_stealth

# Playwright 浏览器安装
playwright install chromium
```

## 与其他爬虫对比

| 特性     | 钛媒体 API | 36 氪 Playwright | 虎嗅 API |
| -------- | ---------- | ---------------- | -------- |
| 速度     | ⭐⭐⭐⭐⭐ | ⭐⭐⭐           | ⭐⭐⭐⭐ |
| 稳定性   | ⭐⭐⭐⭐   | ⭐⭐⭐           | ⭐⭐⭐⭐ |
| 反爬难度 | ⭐⭐       | ⭐⭐⭐⭐⭐       | ⭐⭐⭐   |
| 数据质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐         | ⭐⭐⭐⭐ |

## 更新日志

详见：[CHANGELOG.md](./CHANGELOG.md)

- v2.3.0 (2026-03-30): API + Playwright 混合模式
- v2.2.0 (2026-03-29): Playwright 实时爬虫
