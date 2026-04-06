"""
金融新闻自动化工作流 - 7 大权威媒体
==================================
功能：从 7 大权威科技/财经媒体抓取热点新闻

新闻源：
  1. 虎嗅网 (RSS)      2. 晚点 LatePost (Playwright)  3. 36 氪 (API)
  4. 钛媒体 (RSS)      5. 极客公园 (requests)         6. 界面新闻 (RSS)
  7. 澎湃新闻 (requests)

附注：2晚点、5极客公园、7澎湃新闻，这三个新闻网站由于新闻质量过差，暂时放弃爬取！
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
import time
import base64
import hashlib
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

try:
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

try:
    import cv2
    import numpy as np
    HAS_CV = True
except ImportError:
    HAS_CV = False
    print("⚠️ opencv-python/numpy 未安装，运行：pip install opencv-python numpy")

import random


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


# ==================== 36 氪辅助函数 ====================

def parse_relative_time(time_str: str) -> timedelta:
    """解析时间字符串，返回 timedelta"""
    if not time_str:
        return timedelta(days=999)
    time_str = time_str.strip()
    if time_str == '昨天':
        return timedelta(days=1)
    if time_str == '今天':
        return timedelta(hours=0)
    if time_str == '前天':
        return timedelta(days=2)
    if time_str in ('刚刚', '刚才', '几秒前'):
        return timedelta(seconds=30)

    # 【新增支持】处理"X 小时前"、"X 分钟前"等格式（界面新闻）
    match = re.match(r'(\d+)\s*秒 (前)?', time_str)
    if match:
        return timedelta(seconds=int(match.group(1)))
    match = re.match(r'(\d+)\s*分钟 (前)?', time_str)
    if match:
        return timedelta(minutes=int(match.group(1)))
    match = re.match(r'(\d+)\s*小时 (前)?', time_str)
    if match:
        return timedelta(hours=int(match.group(1)))
    match = re.match(r'(\d+)\s*天 (前)?', time_str)
    if match:
        return timedelta(days=int(match.group(1)))

    # 原有逻辑（兼容其他格式）
    match = re.match(r'(\d+)\s*秒', time_str)
    if match:
        return timedelta(seconds=int(match.group(1)))
    match = re.match(r'(\d+)\s*分钟', time_str)
    if match and ('前' in time_str or '内' in time_str):
        return timedelta(minutes=int(match.group(1)))
    match = re.match(r'(\d+)\s*小时', time_str)
    if match and ('前' in time_str or '内' in time_str):
        return timedelta(hours=int(match.group(1)))
    match = re.match(r'(\d+)\s*天', time_str)
    if match and ('前' in time_str or '内' in time_str):
        return timedelta(days=int(match.group(1)))
    now = datetime.now()
    match = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', time_str)
    if match:
        try:
            year, month, day = int(match.group(1)), int(
                match.group(2)), int(match.group(3))
            article_date = datetime(year, month, day)
            delta = now - article_date
            return delta if delta.total_seconds() >= 0 else timedelta(seconds=0)
        except ValueError:
            pass
    return timedelta(days=999)


def should_continue_fetching(time_str: str, days: int) -> bool:
    """根据发布时间判断是否应该继续抓取

    注意：使用 <= days，即 days 天内的文章都保留
    例如 days=3 时，"3天前"的文章也会被保留
    """
    time_delta = parse_relative_time(time_str)
    # 【修复】使用 <= 而不是 <，确保边界值（如"3天前"）也被包含
    return time_delta.days <= days


def debug_captcha(page, tag="debug"):
    """诊断验证码状态"""
    try:
        captcha_visible = page.evaluate("""() => {
            const container = document.getElementById('captcha_container');
            if (!container) return false;
            const iframe = container.querySelector('iframe');
            return !!(container && iframe && container.offsetParent !== null);
        }""")
        iframe_count = page.locator('iframe[src*="bytedance.com"]').count()
        article_count = len(page.query_selector_all('.information-flow-item'))
        if article_count == 0:
            article_count = len(page.query_selector_all('a[href^="/p/"]'))
        print(f"\n🔍 【诊断】{tag} - {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"   • #captcha_container 是否可见：{captcha_visible}")
        print(f"   • 字节滑块 iframe 数量：{iframe_count}")
        print(f"   • 当前新闻卡片数量：{article_count}")
    except Exception as e:
        print(f"  ⚠️  诊断失败：{e}")


def solve_slider(page):
    """处理滑块验证码"""
    try:
        page.wait_for_timeout(2000)
        captcha_check = page.evaluate("""() => {
            const container = document.getElementById('captcha_container');
            if (!container) return false;
            const iframe = container.querySelector('iframe');
            return !!(container && iframe);
        }""")
        if captcha_check:
            print("  🔒 检测到字节滑块验证码（iframe）...")
            iframe = page.frame_locator('iframe[src*="bytedance.com"]')
            slider_btn = None
            selectors = ['div[class*="slide"]',
                         'div[class*="dragger"]', 'div[class*="captcha"]']
            for sel in selectors:
                try:
                    slider_btn = iframe.locator(sel).first
                    if slider_btn.count() > 0:
                        print(f"  ✅ 找到滑块按钮：{sel}")
                        break
                except:
                    continue
            if slider_btn:
                try:
                    refresh_btn = iframe.locator('text=刷新').first
                    if refresh_btn.count() > 0:
                        refresh_btn.click()
                        print("  🔄 点击了刷新按钮")
                        page.wait_for_timeout(3000)
                except:
                    pass
            else:
                print("  ⚠️  未找到背景图或滑块图")
                try:
                    refresh_btn = iframe.locator('text=刷新').first
                    if refresh_btn.count() > 0:
                        refresh_btn.click()
                        print("  🔄 点击了刷新按钮")
                        page.wait_for_timeout(3000)
                except:
                    pass
    except Exception as e:
        print(f"  ⚠️  验证码处理失败：{e}")


def human_scroll(page, times=30, days: int = 3):
    """
    【最终强化】人类式滚动 + 精准点击"查看更多"按钮
    使用 class="kr-loading-more-button show" + JS 原生点击双保险
    """
    prev_count = 0
    no_new_count = 0
    click_count = 0
    max_clicks = 6

    for i in range(times):
        # 随机鼠标移动（模拟人类）
        for _ in range(random.randint(3, 6)):
            page.mouse.move(random.randint(100, 1400), random.randint(
                100, 800), steps=random.randint(8, 15))
            time.sleep(random.uniform(0.1, 0.4))

        # 大段滚动
        scroll_distance = random.randint(800, 1500)
        page.evaluate(f"window.scrollBy(0, {scroll_distance})")
        time.sleep(random.uniform(2.0, 5.0))

        # 【最终强化】精准点击查看更多按钮
        try:
            more_btn = page.locator('.kr-loading-more-button.show').first
            if more_btn.count() > 0 and click_count < max_clicks:
                print(
                    f"🔄 发现 .kr-loading-more-button.show 按钮，正在点击... (第{click_count+1}次)")

                # 1. 滚动到按钮完全可见
                more_btn.scroll_into_view_if_needed()
                time.sleep(1.0)

                # 2. 先尝试普通点击
                try:
                    more_btn.click()
                    print("  → 使用 Playwright click()")
                except:
                    # 3. 失败则用 JS 原生点击（最强绕过反爬）
                    page.evaluate("""() => {
                        const btn = document.querySelector('.kr-loading-more-button.show');
                        if (btn) btn.click();
                    }""")
                    print("  → 使用 JS 原生 click()")

                click_count += 1

                # 等待新内容加载
                time.sleep(random.uniform(4.0, 7.0))
                debug_captcha(page, f"点击查看更多后_第{i+1}次")

                print(f"  ✅ 已成功点击 '查看更多' 第 {click_count} 次")
        except Exception as e:
            print(f"  ⚠️ 点击'查看更多'失败：{e}")

        # 实时检查最后一条新闻时间
        try:
            last_time = page.evaluate('''() => {
                const items = document.querySelectorAll('.information-flow-item');
                if (items.length === 0) return null;
                const lastItem = items[items.length - 1];
                const timeEl = lastItem.querySelector('.kr-flow-bar-time');
                return timeEl ? timeEl.textContent.trim() : null;
            }''')
            if last_time and not should_continue_fetching(last_time, days):
                print(f"  ✅ 检测到最后一条新闻已超过 {days} 天（{last_time}），停止滚动")
                break
        except Exception as e:
            print(f"  ⚠️ 时间检查失败：{e}")

        # 验证码检查
        if (i + 1) % 3 == 0:
            solve_slider(page)

        # 文章统计 + 卡住处理
        try:
            article_count = len(
                page.query_selector_all('.information-flow-item'))
            if article_count == 0:
                article_count = len(page.query_selector_all('a[href*="/p/"]'))

            if article_count > prev_count:
                no_new_count = 0
                prev_count = article_count
                print(f"  第 {i+1} 次滚动完成，当前文章数：{article_count}")
            else:
                no_new_count += 1
                if no_new_count >= 5:
                    print("  连续无新内容，尝试刷新加载...")
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(2)
                    page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(3)
                    no_new_count = 0
        except:
            pass

        # 诊断（每 5 次）
        if (i + 1) % 5 == 0:
            debug_captcha(page, f"滚动第{i+1}次_后")


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
    """36 氪 - Playwright 动态抓取（带时间智能停止）"""
    name = "36 氪"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        """
        使用 Playwright 抓取 36 氪新闻，根据时间动态判断是否继续

        Args:
            days: 获取最近几天的文章
            filter_companies: 是否过滤公司名

        Returns:
            文章列表
        """
        news_list = []
        urls_seen = set()

        def add_article(title, link, published, source_tag=""):
            """添加文章到列表（自动去重和过滤）"""
            if not title or not link:
                return False
            if link in urls_seen:
                return False
            if filter_companies and not filter_by_companies(title):
                return False
            if published and not should_continue_fetching(published, days):
                return False
            urls_seen.add(link)
            news_list.append({
                "source": "36 氪",
                "title": title.strip(),
                "link": link,
                "published": published or "",
            })
            return True

        # ========== Playwright 抓取 ==========
        if HAS_PLAYWRIGHT:
            pw_count = Source36kr._fetch_playwright(days, add_article)
            print(f"  Playwright: {pw_count}篇新增")
        else:
            print("  Playwright 未安装，跳过")

        print(f"  36 氪最终抓取 {len(news_list)} 条（已去重）")
        return news_list

    @staticmethod
    def _fetch_playwright(days: int, add_article) -> int:
        """
        Playwright 抓取（带完整诊断 + 人类滚动 + 时间智能停止）

        Args:
            days: 获取最近几天的文章
            add_article: 添加文章的函数

        Returns:
            抓取的文章数量
        """
        count = 0

        if not HAS_PLAYWRIGHT:
            print("  ⚠️  Playwright 未安装，跳过")
            return count

        if not HAS_CV:
            print("  ⚠️  OpenCV 未安装，滑块验证可能失败")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-site-isolation-trials',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--window-size=1440,900',
                    ]
                )

                state_path = Path("36kr_state.json")
                if state_path.exists():
                    try:
                        context = browser.new_context(
                            storage_state=json.loads(
                                state_path.read_text(encoding="utf-8"))
                        )
                        print("  📦 加载持久化状态")
                    except:
                        context = browser.new_context()
                else:
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 900},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                        locale="zh-CN",
                        timezone_id="Asia/Shanghai"
                    )

                if HAS_STEALTH:
                    Stealth().apply_stealth_sync(context)

                page = context.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                    window.chrome = { runtime: {} };
                """)

                print("  📡 [Playwright] 访问 36 氪新闻页...")
                page.goto("https://36kr.com/information/web_news/",
                          wait_until="networkidle")
                time.sleep(random.uniform(2.5, 4.5))

                debug_captcha(page, "初始加载")
                solve_slider(page)

                print(f"  开始滚动加载（目标{days}天内，自动停止）...")
                human_scroll(page, times=30, days=days)

                articles_data = page.evaluate('''() => {
                    const result = [];
                    const items = document.querySelectorAll('.information-flow-item');
                    items.forEach(item => {
                        let title = item.querySelector('.article-item-title, .title-wrapper a') ?
                                    item.querySelector('.article-item-title, .title-wrapper a').textContent.trim() : '';
                        let linkEl = item.querySelector('a[href^="/p/"]');
                        let link = linkEl ? linkEl.getAttribute('href') : '';

                        // 【关键修复】精准提取发布时间
                        let publishTime = '';
                        const timeEl = item.querySelector('.kr-flow-bar-time');
                        if (timeEl) {
                            publishTime = timeEl.textContent.trim();
                        }

                        if (title.length > 5 && link) {
                            result.push({
                                title: title,
                                link: link.startsWith('http') ? link : 'https://36kr.com' + link,
                                publishTime: publishTime
                            });
                        }
                    });
                    // 去重
                    const seen = new Set();
                    return result.filter(i => {
                        if (seen.has(i.link)) return false;
                        seen.add(i.link);
                        return true;
                    });
                }''')

                try:
                    context.storage_state(path=str(state_path))
                except:
                    pass

                browser.close()

                filtered_count = 0
                for article in articles_data:
                    publish_time = article.get('publishTime', '')
                    if add_article(article['title'], article['link'], publish_time):
                        count += 1
                        filtered_count += 1

                print(
                    f"  ✅ [Playwright] 提取 {len(articles_data)} 篇，新增 {filtered_count} 篇（时间过滤：{len(articles_data) - filtered_count} 篇）")

        except Exception as e:
            print(f"  ❌ [Playwright] 错误：{e}")
            import traceback
            traceback.print_exc()

        return count


class SourceTmtpost:
    """钛媒体 - API + Playwright 混合抓取（过滤视频新闻）"""
    name = "钛媒体"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        """
        使用 API + Playwright 混合方式抓取钛媒体新闻，过滤视频内容
        优先使用 API 方式（更高效），失败时回退到 Playwright
        """
        # 优先尝试 API 方式
        news_list = SourceTmtpost._fetch_by_api(days, filter_companies)

        if news_list:
            return news_list

        # API 失败时使用 Playwright
        print("  ⚠️ API 方式失败，切换到 Playwright 方式...")
        return SourceTmtpost._fetch_by_playwright(days, filter_companies)

    @staticmethod
    def _fetch_by_api(days: int, filter_companies: bool) -> List[Dict]:
        """通过 API 接口获取钛媒体新闻"""
        if not HAS_REQUESTS:
            return []

        print("  📡 [API] 正在通过 API 获取钛媒体新闻...")

        api_url = "https://api.tmtpost.com/v1/lists/new"
        all_news = []
        urls_seen = set()
        offset = 0
        limit = 20
        max_pages = 30  # 最多获取 30 页（约 600 条）

        # API 参数（基于抓包结果）
        params_template = {
            "limit": str(limit),
            "offset": str(offset),
            "subtype": "post;atlas;video_article;fm_audios;",
        }

        for page in range(max_pages):
            params = params_template.copy()
            params["offset"] = str(offset)

            try:
                # 生成完整的请求头（基于抓包结果）
                timestamp = int(time.time() * 1000)
                token = base64.b64encode(
                    str(timestamp // 1000).encode()).decode()
                auth_str = f"{timestamp // 1000}|F3x47g39Wc4M96nwA28T"
                signature = hashlib.md5(auth_str.encode()).hexdigest()

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "app-key": "2015042403",
                    "app-secret": "F3x47g39Wc4M96nwA28T",
                    "app-version": "web1.0",
                    "device": "pc",
                    "timestamp": str(timestamp),
                    "token": token,
                    "authorization": f'"{timestamp // 1000}|{signature}"',
                    "referer": "https://www.tmtpost.com/",
                    "origin": "https://www.tmtpost.com",
                }

                response = requests.get(
                    api_url, headers=headers, params=params, timeout=15)

                if response.status_code != 200:
                    print(f"  ❌ API 请求失败：{response.status_code}")
                    break

                result = response.json()

                if result.get("result") != "ok":
                    print(f"  ❌ API 返回失败")
                    break

                data = result.get("data", [])

                if not data:
                    break

                # 解析数据
                new_count = 0
                for item in data:
                    item_type = item.get("item_type", "")

                    # 【关键过滤】只保留 post 类型（文字新闻）
                    if item_type != "post":
                        continue

                    title = item.get("title", "")
                    summary = item.get("summary", "")
                    short_url = item.get("short_url", "")
                    time_published = item.get("time_published", "")
                    human_time = item.get("human_time_published", "")

                    # 转换为可读时间
                    publish_time = human_time
                    if time_published:
                        try:
                            ts = int(time_published)
                            publish_time = datetime.fromtimestamp(
                                ts).strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            pass

                    # 去重
                    if short_url in urls_seen:
                        continue

                    urls_seen.add(short_url)

                    # 【需求】合并 title 和 summary 作为标题
                    final_title = f"{title}——{summary}" if summary else title

                    # 公司名过滤
                    if filter_companies and not filter_by_companies(final_title):
                        continue

                    all_news.append({
                        "source": "钛媒体",
                        "title": final_title,
                        "link": short_url,
                        "published": publish_time,
                    })

                    new_count += 1

                print(
                    f"  第{page+1}页：获取 {len(data)} 条，新增 {new_count} 条，总计 {len(all_news)} 条")

                if len(data) < limit:
                    break

                offset += limit

            except Exception as e:
                print(f"  ❌ API 错误：{e}")
                break

        print(f"  ✅ API 方式共获取 {len(all_news)} 条")
        return all_news

    @staticmethod
    def _fetch_by_playwright(days: int, filter_companies: bool) -> List[Dict]:
        """使用 Playwright 浏览器方式获取（备用方案）"""
        if not HAS_PLAYWRIGHT:
            return []

        news_list = []
        urls_seen = set()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled',
                          '--no-sandbox']
                )

                context = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )

                if HAS_STEALTH:
                    Stealth().apply_stealth_sync(context)

                page = context.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = { runtime: {} };
                """)

                print("  📡 [Playwright] 访问钛媒体新闻页...")
                page.goto("https://www.tmtpost.com/new",
                          wait_until="networkidle", timeout=60000)
                time.sleep(random.uniform(2.5, 4.5))

                # 滚动加载
                print("  开始滚动加载...")
                prev_count = 0
                no_new_count = 0

                for i in range(20):
                    page.mouse.move(random.randint(100, 1400),
                                    random.randint(100, 800))
                    page.evaluate(
                        f"window.scrollBy(0, {random.randint(800, 1500)})")
                    time.sleep(random.uniform(2.0, 4.0))

                    try:
                        article_count = len(
                            page.query_selector_all('.type-post'))
                        if article_count > prev_count:
                            no_new_count = 0
                            prev_count = article_count
                        else:
                            no_new_count += 1
                            if no_new_count >= 3:
                                break
                    except:
                        pass

                # 提取文章数据
                articles_data = page.evaluate('''() => {
                    const result = [];
                    const items = document.querySelectorAll('.type-post');
                    items.forEach(item => {
                        const titleEl = item.querySelector('._tit');
                        const title = titleEl ? titleEl.textContent.trim() : '';
                        
                        const linkEl = item.querySelector('._tit');
                        let link = linkEl ? linkEl.getAttribute('href') : '';
                        if (link && !link.startsWith('http')) {
                            link = 'https://www.tmtpost.com' + link;
                        }
                        
                        const timeEl = item.querySelector('._time.newTime');
                        let publishTime = '';
                        if (timeEl) {
                            publishTime = timeEl.textContent.trim().replace('· ', '');
                        }
                        
                        // 只保留文字新闻（链接不包含/video/）
                        if (title.length > 5 && link && !link.includes('/video/')) {
                            result.push({
                                title: title,
                                link: link,
                                publishTime: publishTime
                            });
                        }
                    });
                    return result;
                }''')

                browser.close()

                # 去重并添加到列表
                for article in articles_data:
                    link = article['link']
                    if link not in urls_seen:
                        urls_seen.add(link)

                        # 【需求】只有 title，没有 summary，所以直接用 title
                        final_title = article['title']

                        # 公司名过滤
                        if filter_companies and not filter_by_companies(final_title):
                            continue

                        news_list.append({
                            "source": "钛媒体",
                            "title": final_title,
                            "link": link,
                            "published": article.get('publishTime', ''),
                        })

                print(f"  ✅ Playwright 方式共获取 {len(news_list)} 条")

        except Exception as e:
            print(f"  ❌ [Playwright] 错误：{e}")

        return news_list


class SourceJiemian:
    """界面新闻 - API + Playwright 混合抓取"""
    name = "界面新闻"

    @staticmethod
    def fetch(days: int = 3, filter_companies: bool = False) -> List[Dict]:
        """
        使用 API + Playwright 抓取界面新闻

        Args:
            days: 获取最近几天的文章
            filter_companies: 是否过滤公司名

        Returns:
            文章列表
        """
        news_list = []
        urls_seen = set()

        def add_article(title, link, published):
            """添加文章到列表（自动去重和过滤）"""
            if not title or not link:
                print(f"    ❌ 跳过：标题或链接为空")
                return False
            if link in urls_seen:
                print(f"    ❌ 跳过：重复链接 {link[:50]}")
                return False
            if filter_companies and not filter_by_companies(title):
                print(f"    ❌ 跳过：公司名过滤 {title[:30]}")
                return False
            if published and not should_continue_fetching(published.split(' · ')[-1] if ' · ' in published else published, days):
                print(f"    ❌ 跳过：时间超出范围 {published}")
                return False
            urls_seen.add(link)
            news_list.append({
                "source": "界面新闻",
                "title": title.strip(),
                "link": link,
                "published": published or "",
            })
            print(f"    ✅ 添加：{title[:30]}")
            return True

        # ========== 首页 HTML 抓取（优先，首页有最新文章）==========
        html_count = 0
        if HAS_REQUESTS and HAS_BS4:
            html_count = SourceJiemian._fetch_by_html(days, add_article)
            print(f"  首页HTML: {html_count}篇新增")
        else:
            print("  requests/beautifulsoup4 未安装，跳过首页 HTML 抓取")

        # ========== API 抓取（补充更多文章）==========
        if HAS_REQUESTS:
            api_count = SourceJiemian._fetch_by_api(days, add_article)
            print(f"  API: {api_count}篇新增")
        else:
            print("  requests 未安装，跳过 API 抓取")

        print(f"  界面新闻最终抓取 {len(news_list)} 条（已去重）")
        return news_list

    @staticmethod
    def _fetch_by_html(days: int, add_article) -> int:
        """
        通过解析首页 HTML 获取界面新闻（补充 API 未返回的文章）

        根据抓包分析，首页 HTML 包含：
        - <li class="item"> 中的文章列表
        - 标题在 <div class="title multi-line-overflow"><a> 中
        - 时间在 <div class="info"> 中，格式为 "来源 · X天前"

        Args:
            days: 获取最近几天的文章
            add_article: 添加文章的函数

        Returns:
            抓取的文章数量
        """
        count = 0

        try:
            print("  📄 [HTML] 正在解析首页 HTML...")

            # 获取首页
            html_url = "https://www.jiemian.com/account/main/1.html"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://www.jiemian.com/",
            }

            response = requests.get(html_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"  ❌ 首页请求失败：{response.status_code}")
                return count

            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(response.text, 'html.parser')

            # 解析 <li class="item"> 中的文章
            items = soup.select('li.item')
            print(f"  发现 {len(items)} 个文章条目")

            for item in items:
                try:
                    # 提取标题和链接
                    title_elem = item.select_one('div.title a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')

                    if not title or not link:
                        continue

                    # 提取发布时间和来源
                    info_elem = item.select_one('div.info')
                    published = ""
                    if info_elem:
                        info_text = info_elem.get_text(strip=True)
                        # 格式: "来源 · X天前" 或 "来源 · X小时前"
                        # 按第一个 "·" 分割
                        if '·' in info_text:
                            parts = info_text.split('·', 1)
                            source_name = parts[0].strip()
                            time_str = parts[1].strip() if len(parts) > 1 else ""
                            published = f"{source_name} · {time_str}"
                        else:
                            published = info_text

                    if add_article(title, link, published):
                        count += 1

                except Exception as e:
                    continue

            # 解析 <div class="other-big"> 中的大图文章
            other_big = soup.select('div.other-big a')
            for elem in other_big:
                try:
                    title_elem = elem.select_one('span.title')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = elem.get('href', '')

                    if not title or not link:
                        continue

                    # 提取时间
                    info_elem = elem.select_one('span.info')
                    published = ""
                    if info_elem:
                        info_text = info_elem.get_text(strip=True)
                        if '·' in info_text:
                            parts = info_text.split('·', 1)
                            source_name = parts[0].strip()
                            time_str = parts[1].strip() if len(parts) > 1 else ""
                            published = f"{source_name} · {time_str}"
                        else:
                            published = info_text

                    if add_article(title, link, published):
                        count += 1

                except Exception as e:
                    continue

            # 解析 <div class="other-small"> 中的小图文章
            other_small = soup.select('div.other-small div.item a')
            for elem in other_small:
                try:
                    title_elem = elem.select_one('span.title')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = elem.get('href', '')

                    if not title or not link:
                        continue

                    # 小图文章可能没有时间信息
                    if add_article(title, link, ""):
                        count += 1

                except Exception as e:
                    continue

            print(f"  ✅ 首页 HTML 解析完成：{count}条新增")

        except Exception as e:
            print(f"  ❌ 首页 HTML 解析错误：{e}")

        return count

    @staticmethod
    def _fetch_by_api(days: int, add_article) -> int:
        """
        通过 API 接口获取界面新闻

        Args:
            days: 获取最近几天的文章
            add_article: 添加文章的函数

        Returns:
            抓取的文章数量
        """
        count = 0

        if not HAS_REQUESTS:
            print("  ⚠️  requests 未安装，跳过")
            return count

        try:
            print("  📡 [API] 正在通过 API 获取界面新闻...")

            api_url = "https://papi.jiemian.com/page/api/officialAccount/get_index_lists"
            params = {
                "ckey": "finance_config_index",
                "page": 1
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://www.jiemian.com/",
            }

            all_articles = []
            max_pages = 20  # 最多获取 20 页（每页 10 条，共 200 条）

            for page_num in range(1, max_pages + 1):
                params["page"] = page_num

                try:
                    response = requests.get(
                        api_url, headers=headers, params=params, timeout=10)

                    if response.status_code != 200:
                        print(f"  ❌ API 请求失败：{response.status_code}")
                        break

                    # 【关键修复】处理 JSONP 格式：jsonpReturn({...});
                    content = response.text.strip()

                    # 去除 JSONP 包装，提取 JSON 部分
                    # 格式：jsonpReturn({...});
                    if content.startswith('jsonpReturn(') and content.endswith('});'):
                        json_str = content[12:-2]  # 去掉 'jsonpReturn(' 和 '});'
                    else:
                        json_str = content

                    result = json.loads(json_str)

                    # 检查返回数据
                    if result.get("code") != 0:
                        print(
                            f"  ❌ API 返回错误：{result.get('message', 'unknown error')}")
                        break

                    articles = result.get("result", [])
                    if not articles:
                        print(f"  ⏹️ 第{page_num}页没有数据了，停止")
                        break

                    print(f"  📄 第{page_num}页：{len(articles)}条")

                    # 解析文章
                    for article in articles:
                        title = article.get("title", "")
                        aid = article.get("id", "")
                        source_name = article.get("source_name", "")
                        publish_time = article.get("publish_time_format", "")

                        if not title or not aid:
                            continue

                        link = f"https://www.jiemian.com/article/{aid}.html"
                        published = f"{source_name} · {publish_time}" if source_name and publish_time else ""

                        # 【关键修复】提取纯时间部分用于解析（去掉来源）
                        time_for_parse = publish_time
                        if ' · ' in publish_time:
                            time_for_parse = publish_time.split(
                                ' · ')[-1]  # 取"·"后面的部分

                        # 【调试】输出时间解析结果
                        if count < 3:  # 只显示前 3 条的调试信息
                            print(f"  🔍 文章：{title[:30]}... | 发布时间：{published}")
                            print(f"     用于解析：{time_for_parse}")
                            time_delta = parse_relative_time(time_for_parse)
                            print(
                                f"     解析结果：{time_delta.days}天{time_delta.seconds//3600}小时 | 是否继续：{should_continue_fetching(time_for_parse, days)}")

                        if add_article(title, link, published):
                            count += 1

                    # 【修复】检查本页是否有文章在时间范围内
                    # 如果本页所有文章都超出时间范围，则停止
                    page_has_valid = False
                    for article in articles:
                        publish_time = article.get("publish_time_format", "")
                        if should_continue_fetching(publish_time, days):
                            page_has_valid = True
                            break

                    if not page_has_valid:
                        print(f"  ⏹️ 第{page_num}页所有文章都超出{days}天范围，停止抓取")
                        break

                    # 如果没有更多数据，停止
                    if len(articles) == 0:
                        print(f"  ⏹️ 第{page_num}页没有数据了，停止")
                        break

                    # 短暂延迟，避免触发反爬
                    time.sleep(random.uniform(0.3, 0.8))

                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON 解析错误：{e}")
                    print(f"  原始内容：{content[:200]}")
                    break
                except requests.exceptions.RequestException as e:
                    print(f"  ❌ 网络错误：{e}")
                    break
                except Exception as e:
                    print(f"  ❌ 解析错误：{e}")
                    break

            print(f"  ✅ API 抓取完成：{count}条")
            return count

        except Exception as e:
            print(f"  ❌ 界面新闻 API 错误：{e}")
            import traceback
            traceback.print_exc()
            return count


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
    """保存新闻到 JSON

    Args:
        news_list: 新闻列表
        output_dir: 输出目录（由工作流指定，如 output/pipeline_output_xxx/crawl_news_result/）

    Returns:
        保存的文件路径
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 使用传入的 output_dir，创建目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"news_raw.json"
    filepath = output_path / filename

    # 统计各来源数量
    by_source = {}
    for n in news_list:
        s = n.get("source", "未知")
        by_source[s] = by_source.get(s, 0) + 1

    # 保存为 JSON
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
    parser.add_argument("--output", type=str, default=None, help="输出目录（默认自动创建 output/pipeline_output_时间戳/crawl_news_result/）")
    parser.add_argument("--filter-companies", action="store_true", default=False,
                        help="是否启用公司名过滤（默认关闭，抓取所有新闻）")
    args = parser.parse_args()

    # 如果没有指定输出目录，自动创建工作流输出目录
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path("output") / f"pipeline_output_{timestamp}" / "crawl_news_result"
    else:
        output_dir = Path(args.output)

    # 默认来源
    if args.sources.lower() == "all":
        sources = ["huxiu", "36kr", "tmtpost", "jiemian"]
    else:
        sources = [s.strip() for s in args.sources.split(",")]

    print("=" * 50)
    print("🚀 金融新闻自动化工作流 - 4 大权威媒体")
    print("=" * 50)
    print(f"来源：{', '.join(sources)}")
    print(f"天数：{args.days}")
    print(f"输出目录：{output_dir}")
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
    filepath = save_news(unique, str(output_dir))
    print(f"\n💾 已保存：{filepath}")

    # 输出工作流状态提示
    print(f"\n📋 下一步：运行选题分析，选择要制作的视频主题")


if __name__ == "__main__":
    main()
