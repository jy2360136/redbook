# API参考文档

<cite>
**本文档引用的文件**
- [requirements.txt](file://requirements.txt)
- [financial_news_workflow_crawl4ai.py](file://financial_news_workflow_crawl4ai.py)
- [community_crawler.py](file://community_crawler.py)
- [test_all_sources.py](file://test_all_sources.py)
- [test_crawl4ai.py](file://test_crawl4ai.py)
- [docs/RUN.md](file://docs/RUN.md)
- [docs/SPEC.md](file://docs/SPEC.md)
- [design/design_philosophy.md](file://design/design_philosophy.md)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构概览](#架构概览)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考虑](#性能考虑)
8. [故障排除指南](#故障排除指南)
9. [结论](#结论)
10. [附录](#附录)

## 简介
本项目是一个金融新闻自动化工作流，提供专业的命令行接口用于：
- 从7大权威财经媒体抓取热点新闻
- 从雪球、知乎等社区论坛抓取用户评论和讨论
- 支持公司名过滤、情感分析和批量处理
- 生成分析提示词和内容创作素材

该工作流采用模块化设计，支持异步抓取、错误处理和灵活的参数配置。

## 项目结构
项目采用清晰的模块化组织结构，主要包含以下核心文件：

```mermaid
graph TB
subgraph "核心模块"
A[financial_news_workflow_crawl4ai.py<br/>专业新闻抓取]
B[community_crawler.py<br/>社区论坛抓取]
C[test_all_sources.py<br/>媒体源测试]
D[test_crawl4ai.py<br/>Crawl4AI测试]
end
subgraph "配置文件"
E[requirements.txt<br/>依赖管理]
F[docs/RUN.md<br/>运行文档]
G[docs/SPEC.md<br/>需求规格]
H[design/design_philosophy.md<br/>设计理念]
end
subgraph "输出文件"
I[news_output_crawl4ai_*<br/>新闻数据]
J[community_output_*<br/>评论数据]
K[prompt.txt<br/>分析提示词]
end
A --> I
B --> J
A --> K
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:1-50](file://financial_news_workflow_crawl4ai.py#L1-L50)
- [community_crawler.py:1-50](file://community_crawler.py#L1-L50)

**章节来源**
- [requirements.txt:1-144](file://requirements.txt#L1-L144)
- [docs/RUN.md:1-252](file://docs/RUN.md#L1-L252)

## 核心组件
项目包含两个主要的命令行工具，每个都提供了丰富的功能和参数配置。

### 专业新闻抓取工具
`financial_news_workflow_crawl4ai.py` 提供了7大权威媒体的新闻抓取能力：

**支持的媒体源：**
- 虎嗅网 (RSS)
- 36氪 (API)
- 钛媒体 (RSS)
- 界面新闻 (RSS)
- 极客公园 (Playwright)
- 晚点 LatePost (Playwright)
- 澎湃新闻 (requests)

**核心特性：**
- 多源并行抓取
- 公司名智能过滤
- 自动去重和排序
- JSON格式输出
- 异步/同步双模式支持

**章节来源**
- [financial_news_workflow_crawl4ai.py:94-358](file://financial_news_workflow_crawl4ai.py#L94-L358)
- [docs/SPEC.md:26-45](file://docs/SPEC.md#L26-L45)

### 社区论坛抓取工具
`community_crawler.py` 提供了社区内容的深度抓取能力：

**支持的社区：**
- 雪球网 (xueqiu.com)
- 知乎 (zhihu.com)

**核心特性：**
- 异步并发抓取
- Crawl4AI增强抓取
- HTML内容清理
- 情感分析
- 多种解析策略

**章节来源**
- [community_crawler.py:56-77](file://community_crawler.py#L56-L77)
- [docs/SPEC.md:46-63](file://docs/SPEC.md#L46-L63)

## 架构概览
项目采用分层架构设计，实现了清晰的关注点分离：

```mermaid
graph TB
subgraph "用户接口层"
CLI[命令行接口]
Config[配置管理]
end
subgraph "业务逻辑层"
NewsWorkflow[新闻工作流]
CommunityWorkflow[社区工作流]
FilterEngine[过滤引擎]
Analyzer[分析器]
end
subgraph "数据访问层"
RSSParser[RSS解析器]
APIClient[API客户端]
WebScraper[网页抓取器]
HTMLParser[HTML解析器]
end
subgraph "存储层"
JSONStorage[JSON存储]
Cache[缓存机制]
end
CLI --> NewsWorkflow
CLI --> CommunityWorkflow
Config --> FilterEngine
NewsWorkflow --> RSSParser
NewsWorkflow --> APIClient
CommunityWorkflow --> WebScraper
CommunityWorkflow --> HTMLParser
FilterEngine --> Analyzer
Analyzer --> JSONStorage
WebScraper --> Cache
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:363-453](file://financial_news_workflow_crawl4ai.py#L363-L453)
- [community_crawler.py:413-441](file://community_crawler.py#L413-L441)

## 详细组件分析

### 专业新闻抓取组件

#### 类结构图
```mermaid
classDiagram
class SourceHuxiu {
+string name
+fetch(days, filter_companies) List[Dict]
}
class Source36kr {
+string name
+fetch(days, filter_companies) List[Dict]
}
class SourceTmtpost {
+string name
+fetch(days, filter_companies) List[Dict]
}
class SourceJiemian {
+string name
+fetch(days, filter_companies) List[Dict]
}
class SourceGeekpark {
+string name
+fetch(days, filter_companies) List[Dict]
}
class SourceLatepost {
+string name
+fetch(days, filter_companies) List[Dict]
}
class SourceThepaper {
+string name
+fetch(days, filter_companies) List[Dict]
}
class CommunityCrawler {
+string output_dir
+Dict headers
+List comments_cache
+fetch_all_communities(keyword, sources) List[Dict]
+analyze_sentiment(comments) List[Dict]
+save_comments(comments, keyword) string
}
SourceHuxiu <|-- BaseSource
Source36kr <|-- BaseSource
SourceTmtpost <|-- BaseSource
SourceJiemian <|-- BaseSource
SourceGeekpark <|-- BaseSource
SourceLatepost <|-- BaseSource
SourceThepaper <|-- BaseSource
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:94-358](file://financial_news_workflow_crawl4ai.py#L94-L358)
- [community_crawler.py:82-441](file://community_crawler.py#L82-L441)

#### 新闻抓取序列图
```mermaid
sequenceDiagram
participant User as 用户
participant CLI as 命令行接口
participant Workflow as 新闻工作流
participant Source as 媒体源
participant Parser as 解析器
participant Storage as 存储
User->>CLI : 执行抓取命令
CLI->>Workflow : 解析参数
Workflow->>Source : 初始化媒体源
Workflow->>Source : fetch(days, filter_companies)
Source->>Parser : 解析RSS/API/HTML
Parser-->>Source : 结构化数据
Source-->>Workflow : 新闻列表
Workflow->>Storage : 去重和排序
Storage-->>CLI : 保存JSON文件
CLI-->>User : 输出结果路径
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:363-453](file://financial_news_workflow_crawl4ai.py#L363-L453)

#### 参数配置流程图
```mermaid
flowchart TD
Start([开始]) --> ParseArgs["解析命令行参数"]
ParseArgs --> CheckSources{"检查媒体源参数"}
CheckSources --> |all| UseAll["使用全部7个媒体源"]
CheckSources --> |指定| UseSelected["使用指定媒体源"]
UseAll --> SetDays["设置抓取天数"]
UseSelected --> SetDays
SetDays --> CheckFilter{"检查公司名过滤"}
CheckFilter --> |开启| EnableFilter["启用公司名过滤"]
CheckFilter --> |关闭| DisableFilter["禁用过滤"]
EnableFilter --> FetchNews["抓取新闻"]
DisableFilter --> FetchNews
FetchNews --> Deduplicate["去重处理"]
Deduplicate --> SaveOutput["保存JSON文件"]
SaveOutput --> End([结束])
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:405-453](file://financial_news_workflow_crawl4ai.py#L405-L453)

**章节来源**
- [financial_news_workflow_crawl4ai.py:363-453](file://financial_news_workflow_crawl4ai.py#L363-L453)

### 社区论坛抓取组件

#### 抓取策略类图
```mermaid
classDiagram
class CommunitySource {
+Dict XUEQIU
+Dict ZHIHU
+Dict ALL_SOURCES
}
class CommunityCrawler {
+Path output_dir
+Dict headers
+List comments_cache
+Dict fetch_stats
+fetch_all_communities(keyword, sources) List[Dict]
+fetch_xueqiu_comments(keyword) List[Dict]
+fetch_zhihu_comments(keyword) List[Dict]
+analyze_sentiment(comments) List[Dict]
+save_comments(comments, keyword) string
}
class Crawl4AIEnhanced {
+_fetch_with_crawl4ai_async(url, source_name) string
+_fetch_with_crawl4ai(url, source_name) string
}
class TraditionalHTTP {
+_fetch_with_requests(url, source_name) string
}
CommunityCrawler --> CommunitySource : 使用
CommunityCrawler --> Crawl4AIEnhanced : 增强抓取
CommunityCrawler --> TraditionalHTTP : 传统抓取
```

**图表来源**
- [community_crawler.py:56-176](file://community_crawler.py#L56-L176)
- [community_crawler.py:179-194](file://community_crawler.py#L179-L194)

#### 异步抓取流程图
```mermaid
flowchart TD
Start([开始抓取]) --> InitCrawler["初始化CommunityCrawler"]
InitCrawler --> SelectSources{"选择社区源"}
SelectSources --> |雪球| FetchXueqiu["抓取雪球网"]
SelectSources --> |知乎| FetchZhihu["抓取知乎"]
SelectSources --> |全部| ParallelFetch["并行抓取"]
FetchXueqiu --> TryCrawl4AI["尝试Crawl4AI抓取"]
FetchZhihu --> TryCrawl4AI
TryCrawl4AI --> Crawl4AISuccess{"Crawl4AI成功?"}
Crawl4AISuccess --> |是| ParseHTML["解析HTML内容"]
Crawl4AISuccess --> |否| TryHTTP["尝试HTTP抓取"]
TryHTTP --> HTTPOK{"HTTP成功?"}
HTTPOK --> |是| ParseHTML
HTTPOK --> |否| LogError["记录错误"]
ParseHTML --> CleanContent["清理HTML标签"]
CleanContent --> ExtractData["提取评论数据"]
ExtractData --> StoreCache["存储到缓存"]
StoreCache --> CheckMore{"还有更多源?"}
CheckMore --> |是| SelectSources
CheckMore --> |否| AnalyzeSentiment["情感分析"]
AnalyzeSentiment --> SaveComments["保存评论数据"]
SaveComments --> End([完成])
LogError --> End
```

**图表来源**
- [community_crawler.py:127-176](file://community_crawler.py#L127-L176)
- [community_crawler.py:197-410](file://community_crawler.py#L197-L410)

**章节来源**
- [community_crawler.py:127-441](file://community_crawler.py#L127-L441)

## 依赖分析

### 核心依赖关系
项目采用模块化依赖管理，主要依赖包括：

```mermaid
graph TB
subgraph "网络请求层"
Requests[requests >= 2.31.0]
Httpx[httpx >= 0.27.0]
Aiohttp[aiohttp >= 3.9.0]
end
subgraph "解析层"
Feedparser[feedparser >= 6.0.10]
BeautifulSoup[beautifulsoup4 >= 4.12.0]
Lxml[lxml >= 6.0.2]
end
subgraph "增强爬虫层"
Scrapling[scrapling >= 0.4.0]
Playwright[playwright >= 1.40.0]
Crawl4AI[crawl4ai >= 0.8.0]
end
subgraph "数据处理层"
Orjson[orjson >= 3.11.0]
Pydantic[pydantic >= 2.6.0]
end
subgraph "工具层"
Typer[typer >= 0.9.0]
Click[click >= 8.1.0]
Rich[rich >= 13.9.0]
end
Requests --> Feedparser
Requests --> BeautifulSoup
Playwright --> Crawl4AI
Crawl4AI --> Scrapling
Orjson --> Pydantic
Typer --> Click
```

**图表来源**
- [requirements.txt:7-129](file://requirements.txt#L7-L129)

### 版本兼容性
项目严格管理依赖版本，确保兼容性和稳定性：

**Python版本要求：**
- Python 3.8 或更高版本

**关键依赖版本：**
- requests: >=2.31.0
- feedparser: >=6.0.10  
- beautifulsoup4: >=4.12.0
- playwright: >=1.40.0
- crawl4ai: >=0.8.0

**章节来源**
- [requirements.txt:1-144](file://requirements.txt#L1-L144)
- [docs/RUN.md:19-25](file://docs/RUN.md#L19-L25)

## 性能考虑

### 并行处理策略
项目实现了多层次的并行处理以提升性能：

1. **异步抓取**：使用 asyncio 实现非阻塞网络请求
2. **多源并行**：支持同时抓取多个媒体源
3. **并发解析**：HTML内容解析采用异步策略

### 内存优化
- 使用生成器模式处理大量数据
- 实现增量存储，避免内存溢出
- 智能缓存机制减少重复抓取

### 错误处理机制
- 自动重试策略
- 超时控制和异常捕获
- 降级处理方案

## 故障排除指南

### 常见问题及解决方案

#### 1. 依赖安装失败
**症状：** pip安装依赖时报错
**解决方案：**
```bash
# 升级pip版本
pip install --upgrade pip

# 使用二进制安装
pip install --only-binary :all: -r requirements.txt

# 检查网络连接
pip install --proxy http://user:pass@host:port -r requirements.txt
```

#### 2. Playwright浏览器启动失败
**症状：** 极客公园和晚点新闻抓取失败
**解决方案：**
```bash
# 安装Chromium浏览器
npx playwright install chromium

# 以管理员权限运行
sudo python financial_news_workflow_crawl4ai.py --days 7 --sources geekpark,latepost
```

#### 3. 网站结构变化导致抓取失败
**症状：** 某些媒体源无法获取数据
**解决方案：**
```bash
# 逐步测试媒体源
python test_all_sources.py

# 检查单个媒体源
python -c "
from financial_news_workflow_crawl4ai import SourceHuxiu
news = SourceHuxiu.fetch()
print(f'虎嗅网抓取结果: {len(news)} 条')
"
```

#### 4. Crawl4AI功能异常
**症状：** 社区抓取工具使用Crawl4AI失败
**解决方案：**
```bash
# 测试Crawl4AI功能
python test_crawl4ai.py

# 检查Crawl4AI安装
python -c "from crawl4ai import AsyncWebCrawler; print('Crawl4AI可用')"
```

### 调试技巧
1. **查看详细日志**：运行时会输出详细的抓取过程信息
2. **检查输出文件**：所有抓取的数据都会保存到JSON文件中
3. **使用测试脚本**：通过test_all_sources.py验证各媒体源状态

**章节来源**
- [docs/RUN.md:144-189](file://docs/RUN.md#L144-L189)
- [test_all_sources.py:18-48](file://test_all_sources.py#L18-L48)

## 结论
本项目提供了一个完整、健壮的金融新闻自动化工作流，具有以下优势：

1. **模块化设计**：清晰的职责分离，易于维护和扩展
2. **强大的抓取能力**：支持多种抓取策略和媒体源
3. **灵活的配置**：丰富的命令行参数满足不同需求
4. **完善的错误处理**：健壮的异常处理和降级机制
5. **高性能实现**：异步并发处理，提升整体效率

项目适合金融内容创作者、分析师和媒体从业者使用，能够显著提升内容创作效率和质量。

## 附录

### 命令行接口参考

#### 专业新闻抓取命令
```bash
# 基本用法
python financial_news_workflow_crawl4ai.py --days <天数> --sources <来源>

# 示例命令
python financial_news_workflow_crawl4ai.py --days 10 --sources huxiu,yicai
python financial_news_workflow_crawl4ai.py --days 7 --sources all
python financial_news_workflow_crawl4ai.py --days 5 --sources huxiu,36kr --output ./output
```

**参数说明：**
- `--days`：抓取近X天的新闻（默认3天）
- `--sources`：新闻来源，用逗号分隔（默认all）
- `--output`：输出基础目录（默认当前目录）
- `--filter-companies`：启用公司名过滤（可选）

#### 社区论坛抓取命令
```bash
# 基本用法
python community_crawler.py --keyword <关键词> --sources <来源>

# 示例命令
python community_crawler.py --keyword "小米汽车" --sources all
python community_crawler.py --keyword "华为" --sources xueqiu
python community_crawler.py --keyword "腾讯" --sources zhihu --output ./community_output
```

**参数说明：**
- `--keyword`：搜索关键词（必填）
- `--sources`：社区来源，用逗号分隔（默认all）
- `--output`：输出基础目录（默认当前目录）

### 输出文件格式

#### 新闻数据格式 (news_result.json)
```json
{
  "fetch_time": "2026-03-24T10:26:49.123456",
  "total": 6,
  "by_source": {
    "虎嗅网": 3,
    "36氪": 2,
    "第一财经": 1
  },
  "news": [
    {
      "source": "虎嗅网",
      "title": "小米新SU7，雷军输不起",
      "link": "https://www.huxiu.com/news/12345.html",
      "summary": "文章摘要内容...",
      "published": "2026-03-24 10:00:00"
    }
  ]
}
```

#### 评论数据格式 (comments_关键词.json)
```json
{
  "fetch_time": "2026-03-24T11:12:04.654321",
  "keyword": "小米汽车",
  "total_count": 13,
  "by_source": {
    "雪球网": 5,
    "知乎": 8
  },
  "by_sentiment": {
    "positive": 7,
    "neutral": 4,
    "negative": 2
  },
  "fetch_stats": {
    "xueqiu": {
      "status": "success",
      "count": 5
    },
    "zhihu": {
      "status": "success", 
      "count": 8
    }
  },
  "comments": [
    {
      "source": "雪球网",
      "keyword": "小米汽车",
      "title": "小米汽车发布会观后感",
      "content": "文章内容摘要...",
      "link": "https://www.xueqiu.com/post/12345.html",
      "author": "用户昵称",
      "time": "2026-03-24",
      "like_count": "156",
      "comment_count": "23",
      "fetched_at": "2026-03-24T11:12:04.654321",
      "sentiment": "positive",
      "sentiment_score": 3
    }
  ]
}
```

### 安全和合规注意事项
1. **遵守robots.txt**：尊重网站的爬取规则
2. **合理频率控制**：避免对目标网站造成过大压力
3. **数据使用规范**：仅用于学习和研究目的
4. **隐私保护**：不收集个人敏感信息
5. **版权意识**：仅抓取公开可访问的内容