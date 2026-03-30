# 金融新闻自动化工作流运行文档

## 1. 项目结构

```
redbook/
├── docs/                 # 文档目录
│   ├── CHANGELOG.md      # 更新日志
│   ├── SPEC.md           # 需求文档
│   └── RUN.md            # 运行文档
├── financial_news_workflow_crawl4ai.py  # 专业新闻抓取脚本
├── community_crawler.py  # 社区论坛抓取脚本
├── requirements.txt      # 依赖文件
└── test_playwright.py    # Playwright测试脚本
```

## 2. 环境准备

### 2.1 系统要求

- Windows 10/11
- Python 3.8 或更高版本
- pip 20.0 或更高版本
- 稳定的网络连接
- 至少 1GB 可用磁盘空间

### 2.2 安装步骤

#### 步骤 1: 安装 Python

如果尚未安装 Python，请从 [Python 官方网站](https://www.python.org/downloads/) 下载并安装最新版本的 Python。

#### 步骤 2: 克隆项目代码

```bash
# 克隆项目到本地
git clone <项目地址>
cd redbook
```

#### 步骤 3: 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt
```

#### 步骤 4: 安装 Playwright 浏览器

```bash
# 安装 Chromium 浏览器
npx playwright install chromium
```

## 3. 运行脚本

### 3.1 专业新闻抓取

#### 功能说明

从专业财经媒体抓取深度报道，支持日期过滤和公司名过滤，生成分析提示词。

#### 支持的媒体源

**虎嗅网（v1.3.0 已优化）**：

- 使用官方 API 获取文章列表
- Playwright 批量提取发布时间（相对时间格式）
- 智能时间过滤：动态判断是否继续滚动
- 性能：100% 时间匹配率，智能停止滚动

**36 氪（v2.0.0 已优化）**：

- **新增独立实时爬虫脚本** `crawl_36kr_realtime.py`：
  - **边滚动边保存**：每次滚动后立即提取并实时写入 JSON 文件
  - **智能时间停止**：检测到文章发布时间超过指定天数，立即停止滚动
  - **纯 Playwright 硬核模式**：不依赖 RSS 和 API，完全模拟人类浏览行为
  - **自动破解验证码**：字节跳动滑块验证码 + 自动点击"查看更多"按钮
  - **输出文件**：`36kr_realtime_时间戳.json`

- **旧版主脚本** `financial_news_workflow_crawl4ai.py`（v1.9.0）：
  - **RSS + API + Playwright 三管齐下**，即使 IP 被限制也能稳定获取文章
  - **RSS Feed**：`https://www.36kr.com/feed`，30 篇文章，无验证码
  - **Gateway API**：热榜 16 篇，无需浏览器
  - **Playwright 兜底**：带完整诊断 + 人类滚动 + iframe 滑块破解

- **核心功能**（v2.0.0）：
  - **诊断模式**：自动截图 + 保存 HTML 到 `36kr_debug/` 文件夹，便于调试分析
  - **人类滚动**：随机鼠标移动 + 大段滚动（800-1500px）+ 随机停顿（2.0-5.0 秒），大幅降低验证码触发
  - **OpenCV 缺口检测**：Canny 边缘检测 + 模板匹配，精准计算滑块缺口位置
  - **人类拖动轨迹**：贝塞尔曲线（加速度）+ 随机抖动（±4.5px）+ 到达后微调，模拟真实人类行为
  - **iframe 滑块破解**：`frame_locator` 定位字节跳动验证码，多选择器尝试，自动刷新重试
  - **持久化 Context**：保存登录状态到 `36kr_state.json`，Stealth 反检测，中国浏览器指纹
  - **自动点击"查看更多"**：检测并点击页面底部的"查看更多"按钮，每次点击加载 30 篇新文章，最多点击 6 次
  - **智能时间筛选**：自动提取文章发布时间（支持"X 分钟前"、"昨天"、"2026-03-27"等格式），根据 `--days` 参数过滤超时文章
- **验证码处理**：检测 `#captcha_container` 中的 iframe，OpenCV 缺口识别 + 人类拖动轨迹
- **时间格式支持**：
  - 相对时间："X 分钟前"、"X 小时前"、"X 天前"、"昨天"、"今天"、"前天"、"刚刚"
  - 绝对日期："2026-03-27"、"2026/03/27"、"03-27"、"3 月 27 日"
  - 带时间的绝对日期："2026-03-27 14:30"
- **性能**：
  - v1.6.0: 3 天限制获取 113 篇（RSS 30 + API 65 + Playwright 18），生成 18 个调试文件，0 次验证码触发
  - v1.8.0: 自动点击"查看更多"6 次，加载 210 篇文章（30→60→90→...→210）
  - v1.9.0: 时间过滤 15 篇超时文章，最终获取 248 篇（去重后 239 篇）
  - **v2.0.0**: 纯 Playwright 实时保存，218 篇，实时写入 JSON 文件 6 次

**钛媒体（v2.2.0 已优化）**：

- **独立实时爬虫脚本** `crawl_tmtpost_realtime.py`：
  - **边滚动边保存**：每次滚动后立即提取并实时写入 JSON 文件
  - **智能时间停止**：检测到文章发布时间超过指定天数，立即停止滚动
  - **视频新闻过滤**：只保留文字新闻，自动过滤 `/video/` 链接
  - **输出文件**：`tmtpost_realtime_时间戳.json`

- **主脚本** `financial_news_workflow_crawl4ai.py`：
  - Playwright 滚动加载，支持视频过滤
  - 提取 `.type-post` 类文章，过滤 `.type-video-article`

- **核心功能**：
  - 视频过滤：检测链接是否包含 `/video/`，视频新闻直接跳过
  - 时间提取：从 `._time.newTime` 元素提取发布时间
  - 智能滚动：随机鼠标移动 + 大段滚动 + 随机停顿

- **性能**：
  - 5天模式：抓取 21 篇文字新闻
  - 视频过滤：100% 过滤，0 篇视频混入
  - 时间检测：自动停止，符合要求

**界面新闻（v2.2.0 保留）**：

- RSS 方式：`https://a.jiemian.com/index.php?m=article&a=rss`
- 稳定可靠，50 篇文章

#### 运行命令

```bash
# 基本用法
python financial_news_workflow_crawl4ai.py --days <天数> --sources <来源>

# 示例：抓取近 5 天的钛媒体文字新闻（过滤视频）
python crawl_tmtpost_realtime.py --days 5

# 示例：抓取近 10 天的虎嗅网和钛媒体新闻
python financial_news_workflow_crawl4ai.py --days 10 --sources huxiu,tmtpost

# 示例：抓取所有来源的新闻（4个高质量源）
python financial_news_workflow_crawl4ai.py --days 7 --sources all

# 示例：指定输出目录
python financial_news_workflow_crawl4ai.py --days 5 --sources huxiu,36kr --output ./output
```

#### 参数说明

- `--days`：抓取近X天的新闻（默认2天）
- `--sources`：新闻来源，用逗号分隔（默认all，可选：huxiu,36kr,eastmoney,yicai,stcn,jiemian,caixin,wallstreetcn,jin10,tonghuashun,ftchinese,wsjcn,netease_money,tmtpost,iyiou,ifanr,xinhua08,investing,chinanews,sina_finance,sohu_finance,tencent_finance,cnblogs）
- `--output`：输出基础目录（默认当前目录，会自动创建 news*output_crawl4ai*日期\_时间 子目录）
- `--fixed-output`：固定输出目录（直接使用指定目录，不创建时间戳子目录）

#### 输出结果

- `news_result.json`：包含抓取的新闻数据
- `prompt.txt`：生成的分析提示词

**JSON 输出格式（v1.2.0）**：

```json
{
  "fetch_time": "2026-03-27T15:22:46.208933",
  "total": 1186,
  "by_source": {
    "虎嗅网": 1186
  },
  "news": [
    {
      "source": "虎嗅网",
      "title": "下载量暴跌 65%，那个曾让好莱坞颤抖的 Sora，为何成了 OpenAI 的“弃子”？",
      "link": "https://www.huxiu.com/article/4845990.html",
      "published": "3 分钟前"
    }
  ]
}
```

**注意**：

- v1.2.0 起删除了 `summary` 字段（所有网站都无摘要）
- 虎嗅网使用相对时间格式（如"3 分钟前"）
- 其他网站可能使用 ISO 格式或具体时间

### 3.2 社区论坛抓取

#### 功能说明

从雪球、知乎等社区论坛抓取用户评论和讨论，支持情感分析。

#### 运行命令

```bash
# 基本用法
python community_crawler.py --keyword <关键词> --sources <来源>

# 示例：抓取关于"小米汽车"的所有社区评论
python community_crawler.py --keyword "小米汽车" --sources all

# 示例：只抓取雪球的评论
python community_crawler.py --keyword "华为" --sources xueqiu

# 示例：指定输出目录
python community_crawler.py --keyword "腾讯" --sources zhihu --output ./community_output
```

#### 参数说明

- `--keyword`：搜索关键词（必填，例如：小米汽车）
- `--sources`：社区来源，用逗号分隔（默认all，可选：xueqiu,zhihu）
- `--output`：输出基础目录（默认当前目录，会自动创建 community*output*日期\_时间 子目录）

#### 输出结果

- `comments_<关键词>.json`：包含抓取的评论数据和情感分析结果

## 4. 工作流程示例

### 4.1 完整工作流

1. **步骤 1: 抓取专业新闻**

   ```bash
   python financial_news_workflow_crawl4ai.py --days 10 --sources huxiu,36kr,yicai
   ```

   这将从虎嗅网、36氪和第一财经抓取近10天的新闻，帮助你确定核心选题。

2. **步骤 2: 分析新闻结果**
   查看生成的 `news_result.json` 文件，分析哪些公司或话题被频繁报道，确定你的核心选题。

3. **步骤 3: 抓取社区评论**

   ```bash
   python community_crawler.py --keyword "小米汽车" --sources all
   ```

   针对确定的选题（例如：小米汽车），抓取社区论坛的用户评论和讨论。

4. **步骤 4: 分析社区舆情**
   查看生成的 `comments_小米汽车.json` 文件，分析用户的真实评价和情感倾向。

5. **步骤 5: 生成大纲**
   基于专业新闻和社区评论的分析结果，生成一个包含尽可能多细节的大纲。

6. **步骤 6: 生成逐字稿**
   将大纲输入GPT等AI工具，生成口播逐字稿。

7. **步骤 7: 生成视频**
   将逐字稿输入AI视频工具，生成5分钟左右的视频。

### 4.2 常见问题处理

#### 问题 1: 抓取失败

- 检查网络连接是否正常
- 检查网站是否可以正常访问
- 尝试使用 `--sources` 参数指定更少的来源
- 查看命令行输出的错误信息

#### 问题 2: 36 氪爬取失败（被限流）

- **现象**：Playwright 返回 0 篇文章，或提示验证码处理失败
- **影响**：仅影响 Playwright 部分，RSS + API 不受影响
- **原因**：36 氪对连续快速访问非常敏感，会触发 iframe 滑块验证码
- **解决方法**：
  - v1.5.0 已采用 RSS + API + Playwright 混合策略
  - 即使 Playwright 被拦截，RSS + API 仍可获取 96 篇文章
  - 建议每天爬取 1-2 次，避免频繁访问触发限流

#### 问题 3: Playwright 浏览器启动失败

- 确保已运行 `npx playwright install chromium`
- 检查系统是否有足够的权限
- 尝试以管理员身份运行命令

#### 问题 4: 36 氪验证码处理失败

- **现象**：提示"未找到滑块按钮"
- **原因**：验证码 HTML 结构变化或选择器不匹配
- **解决方法**：
  - 程序会自动截图调试（captcha*debug*\*.png）
  - 检查截图中的验证码结构
  - 已支持多种选择器：`.captcha-slider-btn`、`.dragger-item`、`.captcha_verify_slide--button` 等
  - 如仍失败，请查看截图文件分析原因

#### 问题 5: 依赖安装失败

- 确保pip版本是最新的：`pip install --upgrade pip`
- 尝试使用 `--only-binary :all:` 安装依赖：`pip install --only-binary :all: -r requirements.txt`
- 检查网络连接是否正常

## 5. 技术支持

### 5.1 日志和调试

- 脚本会在运行过程中输出详细的日志信息
- 输出文件会保存在指定的输出目录中
- 可以通过查看日志信息了解抓取过程中的问题

### 5.2 联系方式

- 如有技术问题，请联系项目维护者
- 建议在GitHub上提交Issue

## 6. 注意事项

### 6.1 法律和道德

- 遵守网站的 robots.txt 规则
- 不要过度抓取，避免对目标网站造成负担
- 尊重内容版权，合理使用抓取的信息

### 6.2 性能优化

- 避免同时抓取过多的来源
- 适当设置 `--days` 参数，不要抓取过长时间范围的内容
- 定期清理输出目录，避免磁盘空间不足

### 6.3 维护和更新

- 定期更新依赖库：`pip install --upgrade -r requirements.txt`
- 关注网站结构变化，及时更新抓取规则
- 定期查看更新日志，了解新功能和改进

## 7. 示例输出

### 7.1 专业新闻抓取输出示例

```
📅 日期范围: 2026-03-15 至 2026-03-24 (近 10 天)
--------------------------------------------------
📰 正在抓取 虎嗅网...
   ✅ 虎嗅网: 3 条
📰 正在抓取 36氪...
   ✅ 36氪: 2 条
📰 正在抓取 第一财经...
   ✅ 第一财经: 1 条

📊 共抓取 6 条新闻

📈 各来源统计:
   ✅ huxiu: 3 条
   ✅ 36kr: 2 条
   ✅ yicai: 1 条

🏢 按公司分组:
   小米: 3 条
   华为: 2 条
   腾讯: 1 条

🔥 Top 10 热点新闻:

1. 【虎嗅网】【小米】小米新SU7，雷军输不起
   相关度: ⭐⭐⭐⭐⭐

2. 【36氪】【华为】华为发布新Mate系列，AI功能大幅升级
   相关度: ⭐⭐⭐⭐

3. 【虎嗅网】【小米】新款小米SU7，"融冰"比销量更重要
   相关度: ⭐⭐⭐⭐

💾 新闻已保存到: news_output_crawl4ai_20260324_102649\news_result.json
📝 分析提示词已保存到: news_output_crawl4ai_20260324_102649\prompt.txt
```

### 7.2 社区论坛抓取输出示例

```
🔍 搜索关键词: 小米汽车
--------------------------------------------------
📰 正在抓取 雪球网 关于 '小米汽车' 的讨论...
   ✅ 雪球网: 5 条评论
📰 正在抓取 知乎 关于 '小米汽车' 的讨论...
   ✅ 知乎: 8 条评论

📊 共抓取 13 条评论

📈 各来源统计:
   ✅ xueqiu: 5 条
   ✅ zhihu: 8 条

😊 情感分析结果:
   positive: 7 条
   neutral: 4 条
   negative: 2 条

💾 评论已保存到: community_output_20260324_111204\comments_小米汽车.json
```
