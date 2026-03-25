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


# ==================== 各网站专用爬虫 ====================

class SourceHuxiu:
    """虎嗅网 - RSS"""
    name = "虎嗅网"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        if not HAS_FEEDPARSER:
            return []
        news_list = []
        try:
            feed = feedparser.parse("https://www.huxiu.com/rss/0.xml")
            for entry in feed.entries[:50]:
                title = entry.get("title", "")
                # 可选的公司名过滤
                if filter_companies and not filter_by_companies(title):
                    continue
                news_list.append({
                    "source": "虎嗅网",
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:200],
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"虎嗅网错误：{e}")
        return news_list


class Source36kr:
    """36 氪 - API"""
    name = "36 氪"

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
            news = source_map[src].fetch(days=days, filter_companies=filter_companies)
            print(f"  抓到 {len(news)} 条")
            all_news.extend(news)
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
    all_news = fetch_all(sources, args.days, filter_companies=args.filter_companies)

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
