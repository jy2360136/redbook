# Playwright浏览器自动化

<cite>
**本文档引用的文件**
- [requirements.txt](file://requirements.txt)
- [financial_news_workflow_crawl4ai.py](file://financial_news_workflow_crawl4ai.py)
- [community_crawler.py](file://community_crawler.py)
- [test_all_sources.py](file://test_all_sources.py)
- [test_crawl4ai.py](file://test_crawl4ai.py)
- [news_output_20260323_235950/news_result.json](file://news_output_20260323_235950/news_result.json)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构概览](#架构概览)
5. [详细组件分析](#详细组件分析)
6. [依赖关系分析](#依赖关系分析)
7. [性能考虑](#性能考虑)
8. [故障排除指南](#故障排除指南)
9. [结论](#结论)

## 简介

本项目是一个基于Playwright的浏览器自动化解决方案，专门用于动态网页抓取和新闻聚合。项目实现了7大权威媒体源的自动化抓取，包括极客公园(SourceGeekpark)和晚点(SourceLatepost)等动态加载网站。

项目采用多种抓取策略：
- **Playwright策略**：用于需要JavaScript渲染的动态网站
- **Crawl4AI策略**：AI驱动的网页抓取，支持复杂的反爬机制
- **传统HTTP策略**：适用于静态内容的快速抓取
- **RSS/API策略**：用于订阅源和官方API接口

## 项目结构

```mermaid
graph TB
subgraph "核心模块"
A[financial_news_workflow_crawl4ai.py<br/>主新闻工作流]
B[community_crawler.py<br/>社区论坛抓取]
C[test_all_sources.py<br/>媒体源测试]
D[test_crawl4ai.py<br/>Crawl4AI测试]
end
subgraph "依赖管理"
E[requirements.txt<br/>依赖配置]
end
subgraph "输出文件"
F[news_output_20260323_235950/<br/>抓取结果]
G[crawled_news/<br/>新闻数据]
end
A --> E
B --> E
C --> A
D --> B
A --> F
B --> G
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:1-454](file://financial_news_workflow_crawl4ai.py#L1-L454)
- [community_crawler.py:1-604](file://community_crawler.py#L1-L604)

**章节来源**
- [requirements.txt:1-144](file://requirements.txt#L1-L144)
- [financial_news_workflow_crawl4ai.py:1-454](file://financial_news_workflow_crawl4ai.py#L1-L454)

## 核心组件

### Playwright集成架构

项目实现了两种主要的Playwright集成方式：

1. **同步Playwright模式**：使用`sync_playwright()`上下文管理器
2. **Crawl4AI Playwright模式**：通过AsyncPlaywrightCrawlerStrategy实现

### 媒体源分类

```mermaid
classDiagram
class SourceBase {
+name : str
+fetch(days, filter_companies) List[Dict]
}
class SourceGeekpark {
+name : "极客公园"
+fetch(days, filter_companies) List[Dict]
-sync_playwright() Browser
-extract_news_links(page) List[Dict]
}
class SourceLatepost {
+name : "晚点 LatePost"
+fetch(days, filter_companies) List[Dict]
-sync_playwright() Browser
-scroll_and_extract(page) List[Dict]
}
class SourceHuxiu {
+name : "虎嗅网"
+fetch(days, filter_companies) List[Dict]
-rss_parser() feedparser
}
SourceBase <|-- SourceGeekpark
SourceBase <|-- SourceLatepost
SourceBase <|-- SourceHuxiu
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:215-318](file://financial_news_workflow_crawl4ai.py#L215-L318)

**章节来源**
- [financial_news_workflow_crawl4ai.py:94-358](file://financial_news_workflow_crawl4ai.py#L94-L358)

## 架构概览

```mermaid
sequenceDiagram
participant Main as 主程序
participant Source as 媒体源
participant PW as Playwright
participant Page as 页面
participant Parser as 解析器
Main->>Source : 调用fetch()
Source->>PW : sync_playwright()
PW->>Page : new_page()
Source->>Page : goto(目标URL)
Source->>Page : wait_for_timeout(等待)
Source->>Page : query_selector_all(选择器)
Page-->>Source : 返回元素列表
Source->>Parser : 解析提取内容
Parser-->>Source : 返回新闻列表
Source-->>Main : 返回结果
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:226-263](file://financial_news_workflow_crawl4ai.py#L226-L263)
- [financial_news_workflow_crawl4ai.py:277-318](file://financial_news_workflow_crawl4ai.py#L277-L318)

## 详细组件分析

### SourceGeekpark实现详解

极客公园是典型的需要JavaScript渲染的动态网站，采用了以下策略：

#### 启动流程
```mermaid
flowchart TD
Start([开始抓取]) --> CheckDep{"检查Playwright依赖"}
CheckDep --> |存在| CreateContext["创建sync_playwright上下文"]
CheckDep --> |不存在| ReturnEmpty["返回空列表"]
CreateContext --> LaunchBrowser["启动Chromium浏览器"]
LaunchBrowser --> NewPage["创建新页面"]
NewPage --> Navigate["导航到极客公园首页"]
Navigate --> WaitLoad["等待DOM内容加载完成"]
WaitLoad --> ScrollWait["等待8秒加载动态内容"]
ScrollWait --> ExtractLinks["提取新闻链接"]
ExtractLinks --> FilterLinks["过滤有效链接"]
FilterLinks --> BuildNews["构建新闻对象"]
BuildNews --> CloseBrowser["关闭浏览器"]
CloseBrowser --> End([返回结果])
ReturnEmpty --> End
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:226-263](file://financial_news_workflow_crawl4ai.py#L226-L263)

#### 关键实现要点

1. **浏览器启动配置**：
   - 使用headless=True启用无头模式
   - 设置60秒超时确保页面完全加载
   - 使用wait_until="domcontentloaded"确保DOM内容加载完成

2. **元素选择器策略**：
   ```python
   links = page.query_selector_all('a[href*="/news/"]')
   ```
   - 使用包含"/news/"的链接筛选有效文章
   - 限制提取前30个链接避免过度抓取

3. **反爬虫应对**：
   - 使用set()避免重复URL
   - 实现公司名过滤功能
   - 添加随机等待时间

**章节来源**
- [financial_news_workflow_crawl4ai.py:215-263](file://financial_news_workflow_crawl4ai.py#L215-L263)

### SourceLatepost实现详解

晚点新闻是另一个动态加载的媒体源，采用了更复杂的滚动控制策略：

#### 滚动控制流程
```mermaid
flowchart TD
Start([开始抓取]) --> Navigate["导航到新闻页面"]
Navigate --> InitialWait["等待10秒页面加载"]
InitialWait --> TryWait["尝试等待特定元素"]
TryWait --> ScrollDown["滚动到页面底部"]
ScrollDown --> ScrollWait["等待3秒触发加载"]
ScrollWait --> ScrollUp["滚动到页面顶部"]
ScrollUp --> FinalWait["等待2秒稳定内容"]
FinalWait --> ExtractLinks["提取文章链接"]
ExtractLinks --> FilterLinks["过滤包含dj_detail的链接"]
FilterLinks --> BuildNews["构建新闻对象"]
BuildNews --> CloseBrowser["关闭浏览器"]
CloseBrowser --> End([返回结果])
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:277-318](file://financial_news_workflow_crawl4ai.py#L277-L318)

#### 滚动控制策略

1. **多阶段滚动**：
   - 初始滚动到底部触发懒加载
   - 等待3秒让新内容加载
   - 回滚到顶部确保完整内容

2. **智能等待机制**：
   ```python
   page.wait_for_selector('a[href*="dj_detail"]', timeout=5000)
   ```
   - 尝试等待特定的文章元素
   - 超时后继续执行，提高成功率

3. **链接过滤策略**：
   - 只提取包含"dj_detail"的链接
   - 确保是有效的文章详情页

**章节来源**
- [financial_news_workflow_crawl4ai.py:266-318](file://financial_news_workflow_crawl4ai.py#L266-L318)

### Crawl4AI集成实现

项目实现了Crawl4AI库的双重集成模式：

#### Crawl4AI策略模式
```mermaid
classDiagram
class AsyncWebCrawler {
+crawler_strategy : AsyncCrawlerStrategy
+arun(url, max_depth, max_pages) List[Result]
}
class AsyncPlaywrightCrawlerStrategy {
+supports_playwright : True
+crawl_page(url) HtmlResult
}
class AsyncHTTPCrawlerStrategy {
+supports_playwright : False
+crawl_page(url) HtmlResult
}
AsyncWebCrawler --> AsyncPlaywrightCrawlerStrategy
AsyncWebCrawler --> AsyncHTTPCrawlerStrategy
```

**图表来源**
- [community_crawler.py:127-175](file://community_crawler.py#L127-L175)

#### 异步抓取流程
```mermaid
sequenceDiagram
participant Client as 客户端
participant Crawler as AsyncWebCrawler
participant Strategy as CrawlerStrategy
participant Browser as Playwright浏览器
participant HTTP as HTTP客户端
Client->>Crawler : arun(url, params)
Crawler->>Strategy : 选择策略
alt Playwright策略
Strategy->>Browser : 启动浏览器实例
Browser->>Browser : 导航到页面
Browser->>Browser : 执行JavaScript
Browser-->>Strategy : 返回HTML内容
else HTTP策略
Strategy->>HTTP : 发送HTTP请求
HTTP-->>Strategy : 返回HTML内容
end
Strategy-->>Crawler : 返回抓取结果
Crawler-->>Client : 返回结果列表
```

**图表来源**
- [community_crawler.py:127-175](file://community_crawler.py#L127-L175)

**章节来源**
- [community_crawler.py:125-175](file://community_crawler.py#L125-L175)

### 反爬虫应对策略

项目实现了多层次的反爬虫应对机制：

#### 1. User-Agent轮换
```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
```

#### 2. 多策略降级
```mermaid
flowchart TD
Start([开始抓取]) --> TryPlaywright["尝试Playwright策略"]
TryPlaywright --> PWSuccess{"Playwright成功?"}
PWSuccess --> |是| ReturnPW["返回Playwright结果"]
PWSuccess --> |否| TryCrawl4AI["尝试Crawl4AI策略"]
TryCrawl4AI --> C4AISuccess{"Crawl4AI成功?"}
C4AISuccess --> |是| ReturnC4AI["返回Crawl4AI结果"]
C4AISuccess --> |否| TryHTTP["尝试HTTP策略"]
TryHTTP --> HTTPSuccess{"HTTP成功?"}
HTTPSuccess --> |是| ReturnHTTP["返回HTTP结果"]
HTTPSuccess --> |否| ReturnError["返回错误"]
ReturnPW --> End([结束])
ReturnC4AI --> End
ReturnHTTP --> End
ReturnError --> End
```

#### 3. 动态等待机制
- 使用`wait_for_timeout()`进行固定等待
- 使用`wait_for_selector()`进行条件等待
- 实现智能滚动控制

**章节来源**
- [community_crawler.py:127-175](file://community_crawler.py#L127-L175)
- [financial_news_workflow_crawl4ai.py:226-318](file://financial_news_workflow_crawl4ai.py#L226-L318)

## 依赖关系分析

### 核心依赖架构

```mermaid
graph TB
subgraph "核心依赖"
A[playwright>=1.40.0<br/>浏览器自动化]
B[playwright-stealth>=2.0.0<br/>反检测]
C[scrapling>=0.4.0<br/>反爬虫库]
D[crawl4ai>=0.8.0<br/>AI驱动抓取]
end
subgraph "数据处理"
E[beautifulsoup4>=4.12.0<br/>HTML解析]
F[lxml>=6.0.2<br/>XML解析]
G[feedparser>=6.0.10<br/>RSS解析]
end
subgraph "网络请求"
H[requests>=2.31.0<br/>HTTP客户端]
I[httpx>=0.27.0<br/>异步HTTP]
J[aiohttp>=3.9.0<br/>异步网络]
end
subgraph "工具库"
K[fake-useragent>=2.0.0<br/>User-Agent生成]
L[browserforge>=1.2.0<br/>指纹生成]
M[runtime>=13.9.0<br/>日志显示]
end
A --> C
A --> D
D --> A
E --> F
G --> H
```

**图表来源**
- [requirements.txt:27-35](file://requirements.txt#L27-L35)
- [requirements.txt:16-20](file://requirements.txt#L16-L20)
- [requirements.txt:6-14](file://requirements.txt#L6-L14)

### 组件耦合关系

```mermaid
graph LR
subgraph "抓取层"
A[SourceGeekpark]
B[SourceLatepost]
C[CommunityCrawler]
end
subgraph "策略层"
D[SyncPlaywrightStrategy]
E[Crawl4AIPlaywrightStrategy]
F[HTTPStrategy]
end
subgraph "解析层"
G[BeautifulSoupParser]
H[RSSParser]
I[RegexParser]
end
A --> D
B --> D
C --> E
C --> F
D --> G
E --> G
F --> G
H --> I
```

**图表来源**
- [financial_news_workflow_crawl4ai.py:215-318](file://financial_news_workflow_crawl4ai.py#L215-L318)
- [community_crawler.py:127-175](file://community_crawler.py#L127-L175)

**章节来源**
- [requirements.txt:1-144](file://requirements.txt#L1-144)

## 性能考虑

### 并发优化策略

1. **异步抓取模式**：使用asyncio实现并发抓取
2. **浏览器复用**：在同一浏览器实例中处理多个页面
3. **缓存机制**：避免重复抓取相同内容

### 资源管理

```mermaid
flowchart TD
Start([开始抓取]) --> CreateBrowser["创建浏览器实例"]
CreateBrowser --> CreatePage["创建页面实例"]
CreatePage --> ProcessPage["处理页面内容"]
ProcessPage --> ReusePage["复用页面实例"]
ReusePage --> ProcessNext["处理下一个页面"]
ProcessNext --> ClosePage["关闭页面"]
ClosePage --> CloseBrowser["关闭浏览器"]
CloseBrowser --> End([结束])
```

### 性能监控指标

- **抓取成功率**：统计各媒体源的成功率
- **响应时间**：监控页面加载时间
- **内存使用**：跟踪浏览器内存占用
- **错误率**：记录各种异常类型

## 故障排除指南

### 常见问题及解决方案

#### 1. Playwright安装问题
```bash
# 安装Playwright浏览器
playwright install chromium
```

#### 2. 依赖冲突解决
```bash
# 升级所有依赖
pip install -r requirements.txt --upgrade
```

#### 3. 网络连接问题
- 检查代理设置
- 验证防火墙配置
- 测试DNS解析

#### 4. 页面加载失败
```python
# 增加超时时间
page.goto(url, timeout=90000)

# 使用更宽松的等待条件
page.wait_for_load_state("networkidle")
```

### 调试技巧

1. **启用调试模式**：
   ```python
   browser = p.chromium.launch(headless=False, slow_mo=100)
   ```

2. **截图调试**：
   ```python
   page.screenshot(path="debug.png", full_page=True)
   ```

3. **控制台日志**：
   ```python
   page.on("console", lambda msg: print(f"控制台: {msg.text}"))
   ```

**章节来源**
- [requirements.txt:139-143](file://requirements.txt#L139-L143)

## 结论

本项目展示了现代浏览器自动化抓取的最佳实践，通过多种策略的组合实现了高成功率的动态网页抓取。主要特点包括：

1. **多策略架构**：Playwright、Crawl4AI、HTTP三种策略的智能切换
2. **反爬虫应对**：多层次的反检测机制和降级策略
3. **性能优化**：异步处理、资源复用和智能等待
4. **可扩展性**：模块化的媒体源设计，易于添加新的抓取目标

对于开发者而言，该项目提供了完整的Playwright使用示例，包括浏览器启动、页面导航、元素选择器、JavaScript执行和截图功能的实现方案。同时，项目中的反爬虫策略和性能优化技巧为生产环境的部署提供了宝贵的实践经验。