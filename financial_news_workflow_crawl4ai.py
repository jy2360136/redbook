"""
金融新闻自动化工作流 - 7 大权威媒体
==================================
功能：从 7 大权威科技/财经媒体抓取热点新闻

新闻源：
  1. 虎嗅网 (RSS)      2. 晚点 LatePost (Playwright)  3. 36 氪 (API)
  4. 钛媒体 (RSS)      5. 极客公园 (requests)         6. 界面新闻 (RSS)
  7. 澎湃新闻 (requests)
"""

import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import argparse
import html
import re
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

# 尝试导入依赖
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("⚠️ feedparser 未安装，运行：pip install feedparser")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️ requests 未安装，运行：pip install requests")

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("⚠️ playwright 未安装，运行：pip install playwright && playwright install chromium")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️ beautifulsoup4 未安装，运行：pip install beautifulsoup4")


# ==================== 配置 ====================

# 中国知名公司名单（暂时写死，后续重构为可配置模块）
FAMOUS_COMPANIES = [
    "比亚迪", "小鹏", "蔚来", "理想", "小米", "吉利", "华为", "腾讯", "阿里",
    "字节", "百度", "京东", "美团", "拼多多", "网易", "快手", "B 站",
    "宁德时代", "茅台", "五粮液", "伊利", "蒙牛", "安踏", "李宁", "万科",
]

# 公司名过滤模块（暂时禁用，等待后续重构）


def filter_by_companies(title: str, companies: list = None) -> bool:
    """
    根据公司名过滤标题

    Args:
        title: 新闻标题
        companies: 公司名列表，为 None 时使用 FAMOUS_COMPANIES

    Returns:
        bool: 是否包含公司名
    """
    if companies is None:
        companies = FAMOUS_COMPANIES
    return any(c in title for c in companies)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def batch_fetch_huxiu_times(news_list: List[Dict]) -> List[Dict]:
    """
    批量获取虎嗅文章的真实发布时间
    从 https://www.huxiu.com/article/ 页面直接提取所有文章的时间

    Args:
        news_list: 新闻列表

    Returns:
        更新后的新闻列表
    """
    try:
        from playwright.sync_api import sync_playwright

        # 收集所有虎嗅文章的 URL
        huxiu_articles = [n for n in news_list if n.get("source") == "虎嗅网"]

        if not huxiu_articles:
            return news_list

        print(f"  发现 {len(huxiu_articles)} 篇虎嗅文章，正在获取真实发布时间...")

        # 启动浏览器
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 访问文章列表页
            print("  正在访问 https://www.huxiu.com/article/...")
            page.goto("https://www.huxiu.com/article/",
                      wait_until="networkidle", timeout=30000)

            # 滚动加载所有文章
            print("  正在滚动加载更多文章...")
            last_height = page.evaluate("() => document.body.scrollHeight")
            max_scrolls = 50  # 最多滚动 50 次
            scrolls = 0

            while scrolls < max_scrolls:
                # 滚动到底部
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)  # 等待 2 秒加载新内容

                new_height = page.evaluate("() => document.body.scrollHeight")
                if new_height == last_height:
                    # 没有更多内容了
                    break
                last_height = new_height
                scrolls += 1
                print(
                    f"    已滚动 {scrolls} 次，当前文章数：{len(page.query_selector_all('.card'))}")

            print(f"  滚动完成，共滚动 {scrolls} 次")

            # 提取所有文章的链接和时间
            # HTML 结构：<div class="bottom-line__time">3 小时前</div>
            articles_data = page.evaluate('''
                () => {
                    const items = document.querySelectorAll('.card');
                    const result = [];
                    items.forEach(item => {
                        const linkElem = item.querySelector('a[href*="/article/"]');
                        const timeElem = item.querySelector('.bottom-line__time');
                        if (linkElem && timeElem) {
                            result.push({
                                url: linkElem.href,
                                time: timeElem.textContent.trim()
                            });
                        }
                    });
                    return result;
                }
            ''')

            browser.close()

            # 创建 URL 到时间的映射
            time_map = {item['url']: item['time'] for item in articles_data}
            print(f"  从列表页提取到 {len(time_map)} 篇文章的时间")

            # 更新时间到新闻列表
            matched = 0
            for article in huxiu_articles:
                url = article.get("link")
                if url in time_map:
                    article["published"] = time_map[url]
                    matched += 1
                else:
                    # 如果找不到，使用当前时间
                    article["published"] = datetime.now().isoformat()

            print(f"  ✅ 成功匹配 {matched}/{len(huxiu_articles)} 篇文章的时间")

    except Exception as e:
        print(f"  ❌ 批量获取失败：{e}")
        # 出错时给所有虎嗅文章设置当前时间
        for article in news_list:
            if article.get("source") == "虎嗅网":
                article["published"] = datetime.now().isoformat()

    return news_list

# ==================== 各网站专用爬虫 ====================


class SourceHuxiu:
    """虎嗅网 - 直接调用 API（已攻克 WAF）"""
    name = "虎嗅网"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        """
        通过 API 获取虎嗅文章

        Args:
            days: 获取最近几天的文章（暂未实现时间过滤）
            filter_companies: 是否过滤公司名

        Returns:
            文章列表
        """
        api_url = "https://api-article.huxiu.com/web/channel/articleListV1"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Referer": "https://www.huxiu.com/",
            "Origin": "https://www.huxiu.com",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        news_list = []
        last_id = ""
        max_pages = 50  # 最多获取 50 页（约 1200 篇）

        print("  正在通过 API 获取文章...")

        for page in range(max_pages):
            # 构造 POST 数据
            data = f"platform=www&channel_id=0&last_id={last_id}" if last_id else "platform=www&channel_id=0"

            try:
                response = requests.post(
                    api_url, headers=headers, data=data, timeout=10)

                if response.status_code != 200:
                    print(f"  ❌ 第{page+1}页请求失败：{response.status_code}")
                    break

                result = response.json()

                if not result.get("success"):
                    print(f"  ❌ API 返回失败：{result.get('message')}")
                    break

                # 解析数据
                data_content = result.get("data", {})
                datalist = data_content.get("datalist", [])

                if not datalist:
                    print(f"  ✅ 已无更多内容")
                    break

                # 提取文章
                for item in datalist:
                    aid = item.get("aid")
                    title = item.get("title", "")
                    url = item.get(
                        "url", f"https://www.huxiu.com/article/{aid}.html")

                    # 确保 URL 格式正确
                    if not url.startswith("http"):
                        url = f"https://www.huxiu.com/article/{aid}.html"

                    # 公司名过滤
                    if filter_companies and not filter_by_companies(title):
                        continue

                    news_list.append({
                        "source": "虎嗅网",
                        "title": title,
                        "link": url,
                    })

                print(
                    f"  第{page+1}页：获取到 {len(datalist)} 篇文章，共 {len(news_list)} 篇")

                # 更新 last_id
                last_id = data_content.get("last_id", "")

                if not last_id:
                    print(f"  ✅ 已获取所有文章")
                    break

            except Exception as e:
                print(f"  ❌ 错误：{e}")
                break

        print(f"  成功抓取 {len(news_list)} 条")
        return news_list


class SourceLatePost:
    """晚点 LatePost - Playwright 动态抓取"""
    name = "晚点 LatePost"


class Source36kr:

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        if not HAS_REQUESTS:
            return []
        news_list = []
        try:
            resp = requests.get(
                "https://36kr.com/api/newsflash",
                headers=HEADERS,
                params={"page": 1, "page_size": 50},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", {}).get("items", [])
                for item in items:
                    title = item.get("title", "")
                    # 可选的公司名过滤
                    if filter_companies and not filter_by_companies(title):
                        continue
                    news_list.append({
                        "source": "36 氪",
                        "title": title,
                        "link": f"https://36kr.com/newsflashes/{item.get('id', '')}",
                        "summary": item.get("description", "")[:200],
                        "published": str(item.get("published_at", "")),
                    })
        except Exception as e:
            print(f"36 氪错误：{e}")
        return news_list


class SourceTmtpost:
    """钛媒体 - RSS"""
    name = "钛媒体"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        if not HAS_FEEDPARSER:
            return []
        news_list = []
        try:
            feed = feedparser.parse("https://www.tmtpost.com/rss.xml")
            for entry in feed.entries[:50]:
                title = entry.get("title", "")
                # 可选的公司名过滤
                if filter_companies and not filter_by_companies(title):
                    continue
                news_list.append({
                    "source": "钛媒体",
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:200],
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"钛媒体错误：{e}")
        return news_list


class SourceJiemian:
    """界面新闻 - RSS"""
    name = "界面新闻"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        if not HAS_FEEDPARSER:
            return []
        news_list = []
        try:
            feed = feedparser.parse(
                "https://a.jiemian.com/index.php?m=article&a=rss")
            for entry in feed.entries[:50]:
                title = entry.get("title", "")
                # 可选的公司名过滤
                if filter_companies and not filter_by_companies(title):
                    continue
                news_list.append({
                    "source": "界面新闻",
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:200],
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"界面新闻错误：{e}")
        return news_list


class SourceGeekpark:
    """极客公园 - Playwright 抓取（反爬机制需要浏览器）"""
    name = "极客公园"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        if not HAS_PLAYWRIGHT:
            print("极客公园：需要 playwright")
            return []
        news_list = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                print("  正在访问极客公园...")
                page.goto("https://www.geekpark.net/", timeout=60000,
                          wait_until="domcontentloaded")
                # 等待页面加载完成
                page.wait_for_timeout(8000)

                # 查找所有新闻链接
                links = page.query_selector_all('a[href*="/news/"]')
                print(f"  找到 {len(links)} 个文章链接")

                urls_seen = set()
                for link in links[:30]:
                    href = link.get_attribute('href')
                    text = link.text_content().strip()
                    # 确保是 /news/xxxxxx 格式
                    if href and re.search(r'/news/\d+', href):
                        full_url = href if href.startswith(
                            'http') else f'https://www.geekpark.net{href}'
                        if full_url not in urls_seen:
                            urls_seen.add(full_url)
                            # 可选的公司名过滤
                            if not filter_companies or filter_by_companies(text):
                                news_list.append({
                                    "source": "极客公园",
                                    "title": text[:100],
                                    "link": full_url,
                                    "summary": text[:200],
                                    "published": datetime.now().isoformat(),
                                })

                browser.close()
                print(f"  成功抓取 {len(news_list)} 条")
        except Exception as e:
            print(f"极客公园错误：{e}")
        return news_list


class SourceLatepost:
    """晚点 LatePost - Playwright 抓取（动态加载）"""
    name = "晚点 LatePost"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        if not HAS_PLAYWRIGHT:
            print("晚点：需要 playwright")
            return []
        news_list = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                print("  正在访问晚点 LatePost...")
                page.goto("https://www.latepost.com/news",
                          timeout=90000, wait_until="domcontentloaded")
                # 等待新闻列表加载完成
                page.wait_for_timeout(10000)
                # 尝试等待具体的文章元素出现
                try:
                    page.wait_for_selector(
                        'a[href*="dj_detail"]', timeout=5000)
                except:
                    pass  # 继续执行，即使没有等到特定元素
                # 向下滚动页面以触发更多内容加载
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(3000)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(2000)

                # 查找所有文章链接（使用更宽泛的选择器）
                links = page.query_selector_all('a[href*="/news/"]')
                print(f"  找到 {len(links)} 个文章链接")
                for link in links[:30]:
                    href = link.get_attribute('href')
                    text = link.text_content().strip()
                    # 过滤出包含 dj_detail 的链接
                    if href and 'dj_detail' in href and text:
                        # 可选的公司名过滤
                        if not filter_companies or filter_by_companies(text):
                            news_list.append({
                                "source": "晚点 LatePost",
                                "title": text[:100],
                                "link": f"https://www.latepost.com{href}",
                                "summary": text[:200],
                                "published": datetime.now().isoformat(),
                            })
                browser.close()
                print(f"  成功抓取 {len(news_list)} 条")
        except Exception as e:
            print(f"晚点错误：{e}")
        return news_list


class SourceThepaper:
    """澎湃新闻 - requests 抓取"""
    name = "澎湃新闻"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        if not HAS_REQUESTS:
            return []
        news_list = []
        try:
            resp = requests.get("https://m.thepaper.cn/",
                                headers=HEADERS, timeout=15)
            html = resp.text
            ids = re.findall(r'newsDetail_forward_(\d+)', html)
            print(f"  澎湃新闻：找到 {len(ids)} 个文章 ID")
            for aid in ids[:30]:
                url = f"https://m.thepaper.cn/newsDetail_forward_{aid}"
                try:
                    r = requests.get(url, headers=HEADERS, timeout=10)
                    title_match = re.search(r'<title>([^<]+)</title>', r.text)
                    if title_match:
                        title = title_match.group(1).strip()
                        if '_澎湃新闻' in title:
                            title = title.split('_澎湃新闻')[0].strip()
                        # 可选的公司名过滤
                        if not filter_companies or filter_by_companies(title):
                            news_list.append({
                                "source": "澎湃新闻",
                                "title": title[:100],
                                "link": url,
                                "summary": title[:200],
                                "published": datetime.now().isoformat(),
                            })
                except:
                    continue
        except Exception as e:
            print(f"澎湃新闻错误：{e}")
        return news_list


# ==================== 主程序 ====================

def fetch_all(sources: List[str], days: int, filter_companies: bool = False) -> List[Dict]:
    """抓取指定来源的新闻"""
    all_news = []
    source_map = {
        "huxiu": SourceHuxiu,
        "36kr": Source36kr,
        "tmtpost": SourceTmtpost,
        "jiemian": SourceJiemian,
        "geekpark": SourceGeekpark,
        "latepost": SourceLatepost,
        "thepaper": SourceThepaper,
    }
    for src in sources:
        if src in source_map:
            print(f"\n正在抓取：{source_map[src].name}...")
            news = source_map[src].fetch(
                days=days, filter_companies=filter_companies)
            print(f"  抓到 {len(news)} 条")
            all_news.extend(news)

    # 批量获取虎嗅文章的发布时间
    if "huxiu" in sources:
        print("\n正在获取虎嗅文章的真实发布时间...")
        all_news = batch_fetch_huxiu_times(all_news)

    return all_news


def save_news(news_list: List[Dict], output_dir: str) -> str:
    """保存新闻到 JSON"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # 创建带时间戳的输出目录
    output_path = Path(f"news_output_crawl4ai_{timestamp}")
    output_path.mkdir(exist_ok=True)
    filepath = output_path / f"news_result.json"
    by_source = {}
    for n in news_list:
        s = n.get("source", "未知")
        by_source[s] = by_source.get(s, 0) + 1
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            "fetch_time": datetime.now().isoformat(),
            "total": len(news_list),
            "by_source": by_source,
            "news": news_list,
        }, f, ensure_ascii=False, indent=2)
    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="金融新闻自动化工作流 - 7 大权威媒体")
    parser.add_argument("--days", type=int, default=3, help="抓取近 X 天")
    parser.add_argument("--sources", type=str, default="all", help="来源，逗号分隔")
    parser.add_argument("--output", type=str, default=".", help="输出目录")
    parser.add_argument("--filter-companies", action="store_true", default=False,
                        help="是否启用公司名过滤（默认关闭，抓取所有新闻）")
    args = parser.parse_args()

    # 默认来源
    if args.sources.lower() == "all":
        sources = ["huxiu", "36kr", "tmtpost", "jiemian",
                   "geekpark", "latepost", "thepaper"]
    else:
        sources = [s.strip() for s in args.sources.split(",")]

    print("=" * 50)
    print("🚀 金融新闻自动化工作流 - 7 大权威媒体")
    print("=" * 50)
    print(f"来源：{', '.join(sources)}")
    print(f"天数：{args.days}")
    print(f"公司名过滤：{'✅ 开启' if args.filter_companies else '❌ 关闭'}")

    # 抓取
    all_news = fetch_all(sources, args.days,
                         filter_companies=args.filter_companies)

    # 去重
    seen = set()
    unique = []
    for n in all_news:
        t = n.get("title", "")
        if t and t not in seen:
            seen.add(t)
            unique.append(n)

    print(f"\n总计：{len(unique)} 条（去重后）")

    # 显示
    print("\nTop 10:")
    for i, n in enumerate(unique[:10], 1):
        print(f"  {i}. [{n['source']}] {n['title'][:40]}")

    # 保存
    filepath = save_news(unique, args.output)
    print(f"\n💾 已保存：{filepath}")


if __name__ == "__main__":
    main()
