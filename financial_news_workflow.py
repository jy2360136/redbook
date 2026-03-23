"""
金融新闻自动化工作流 - 第一步：新闻抓取与分析
====================================
功能：从中国主流财经媒体抓取热点新闻，生成小红书风格的财经分析文稿

数据源：
【RSS源】
- 虎嗅网 (huxiu.com)
- 第一财经 (yicai.com)
- 证券时报网 (stcn.com)
- 界面新闻 (jiemian.com)
- 财新网 (caixin.com) - FeedX
- FT中文网 (ftchinese.com)
- 华尔街日报中文版 (wsj.com)
- 网易财经 (money.163.com)
- 钛媒体 (tmtpost.com)
- 亿欧网 (iyiou.com)
- 爱范儿 (ifanr.com)
- 中国金融信息网 (xinhua08.com)
- Investing.com中文 (cn.investing.com)
- 中国新闻网财经 (chinanews.com)
- 新浪财经 (finance.sina.com.cn)

【API源】
- 36氪 (36kr.com)
- 东方财富 (eastmoney.com)
- 雪球 (xueqiu.com)
- 华尔街见闻 (wallstreetcn.com)
- 金十数据 (jin10.com)

【已禁用】
- 财联社 (cls.cn) - API已失效
- 同花顺 (10jqka.com.cn) - 需要网页抓取
"""

import sys
import io
import re
import argparse
import html

# 中国知名公司名单（家喻户晓的中国公司）
FAMOUS_CHINESE_COMPANIES = [
    # 汽车行业
    "比亚迪", "小鹏", "蔚来", "理想", "小米", "吉利", "长城", "奇瑞", "广汽", "上汽",
    "红旗", "东风", "长安", "五菱", "鸿蒙智行", "问界", "智界", "享界", "尊界",
    # 科技互联网
    "华为", "腾讯", "阿里", "阿里巴巴", "字节", "抖音", "百度", "京东", "美团", "拼多多",
    "网易", "快手", "B站", "哔哩哔哩", "微博", "滴滴", "大疆", "OPPO", "vivo", "荣耀",
    "海康威视", "科大讯飞", "商汤", "旷视", "寒武纪",
    # 新能源/电池
    "宁德时代", "亿纬锂能", "国轩高科", "欣旺达", "天齐锂业", "赣锋锂业",
    # 家电
    "美的", "格力", "海尔", "海信", "TCL", "创维", "老板电器", "苏泊尔", "九阳", "小熊",
    # 消费/零售
    "茅台", "五粮液", "伊利", "蒙牛", "农夫山泉", "海天", "金龙鱼", "安踏", "李宁", "特步",
    "泡泡玛特", "名创优品",
    # 金融
    "工商银行", "建设银行", "农业银行", "中国银行", "招商银行", "平安", "中国人寿",
    "中信证券", "华泰证券", "东方财富",
    # 房地产
    "万科", "碧桂园", "恒大", "融创", "保利", "华润",
    # 航空航天/军工
    "中国商飞", "中航工业", "航天科技",
    # 其他
    "联想", "中兴", "京东方", "立讯精密", "歌尔股份", "三一重工", "中联重科",
    "顺丰", "中通", "圆通", "韵达", "申通",
]

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from pathlib import Path

# 尝试导入可选依赖
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️  BeautifulSoup4 未安装，部分功能受限。运行: pip install beautifulsoup4")

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("⚠️  feedparser 未安装，RSS功能受限。运行: pip install feedparser")

# Scrapling - 增强反爬能力
try:
    from scrapling.fetchers import StealthyFetcher, DynamicFetcher
    HAS_SCRAPLING = True
    print("✅ Scrapling 已安装，反爬功能已启用")
except ImportError:
    HAS_SCRAPLING = False
    print("⚠️  Scrapling 未安装，反爬能力受限。运行: pip install scrapling")
    print("   安装后可增强对雪球、36kr等难爬网站的支持")


# ==================== 新闻源配置 ====================

class NewsSource:
    """新闻源配置 - 所有支持的财经媒体"""

    # 原有来源
    HUXIU = {
        "name": "虎嗅网",
        "base_url": "https://www.huxiu.com",
        "rss_url": "https://www.huxiu.com/rss/0.xml",
        "type": "rss"
    }

    KR36 = {
        "name": "36氪",
        "base_url": "https://36kr.com",
        "api_url": "https://36kr.com/api/newsflash",  # 更新为新API地址
        "type": "api"
    }

    XUEQIU = {
        "name": "雪球",
        "base_url": "https://xueqiu.com",
        "hot_url": "https://xueqiu.com/statuses/hot/listV2.json",
        "type": "api"
    }

    CLS = {
        "name": "财联社",
        "base_url": "https://www.cls.cn",
        # 原API已失效，暂时禁用
        "type": "disabled"
    }

    # 新增来源
    EASTMONEY = {
        "name": "东方财富",
        "base_url": "https://www.eastmoney.com",
        "api_url": "https://newsapi.eastmoney.com/kuaixun/v1/kuaixun/getlist_102_ajaxResult_50_1_.html",
        "type": "api"
    }

    YICAI = {
        "name": "第一财经",
        "base_url": "https://www.yicai.com",
        "rss_url": "https://www.yicai.com/feed",
        "type": "rss"
    }

    STCN = {
        "name": "证券时报网",
        "base_url": "https://www.stcn.com",
        "rss_url": "https://www.stcn.com/rss.xml",
        "type": "rss"
    }

    JIEMIAN = {
        "name": "界面新闻",
        "base_url": "https://www.jiemian.com",
        "rss_url": "https://a.jiemian.com/index.php?m=article&a=rss",
        "type": "rss"
    }

    CAIXIN = {
        "name": "财新网",
        "base_url": "https://www.caixin.com",
        "rss_url": "https://feedx.net/rss/caixin.xml",
        "type": "rss"
    }

    WALLSTREETCN = {
        "name": "华尔街见闻",
        "base_url": "https://wallstreetcn.com",
        "api_url": "https://api-one.wallstreetcn.com/apiv1/content/articles",
        "type": "api"
    }

    JIN10 = {
        "name": "金十数据",
        "base_url": "https://www.jin10.com",
        "api_url": "https://flash-api.jin10.com/get_flash_list",
        "type": "api"
    }

    TONGHUASHUN = {
        "name": "同花顺",
        "base_url": "https://www.10jqka.com.cn",
        "api_url": "https://news.10jqka.com.cn/guonei_list.shtml",
        "type": "web"
    }

    # ==================== 新增RSS源 ====================

    FTCHINESE = {
        "name": "FT中文网",
        "base_url": "https://www.ftchinese.com",
        "rss_url": "https://www.ftchinese.com/rss/news",
        "type": "rss"
    }

    WSJCN = {
        "name": "华尔街日报中文版",
        "base_url": "https://cn.wsj.com",
        "rss_url": "https://feeds.feedburner.com/wsjtou-teng",
        "type": "rss"
    }

    NETEASE_MONEY = {
        "name": "网易财经",
        "base_url": "https://money.163.com",
        "rss_url": "https://money.163.com/special/00252EQ2/moneyrss.html",
        "type": "rss"
    }

    TMTPOST = {
        "name": "钛媒体",
        "base_url": "https://www.tmtpost.com",
        "rss_url": "https://www.tmtpost.com/rss.xml",
        "type": "rss"
    }

    IYIOU = {
        "name": "亿欧网",
        "base_url": "https://www.iyiou.com",
        "rss_url": "https://www.iyiou.com/rss",
        "type": "rss"
    }

    IFANR = {
        "name": "爱范儿",
        "base_url": "https://www.ifanr.com",
        "rss_url": "https://www.ifanr.com/feed",
        "type": "rss"
    }

    XINHUA08 = {
        "name": "中国金融信息网",
        "base_url": "http://www.xinhua08.com",
        "rss_url": "http://app.xinhua08.com/rss.php",
        "type": "rss"
    }

    INVESTING = {
        "name": "Investing.com中文",
        "base_url": "https://cn.investing.com",
        "rss_url": "https://cn.investing.com/rss/news.rss",
        "type": "rss"
    }

    CHINANEWS = {
        "name": "中国新闻网财经",
        "base_url": "https://www.chinanews.com",
        "rss_url": "https://www.chinanews.com.cn/rss/finance.xml",
        "type": "rss"
    }

    SINA_FINANCE = {
        "name": "新浪财经",
        "base_url": "https://finance.sina.com.cn",
        "rss_url": "https://finance.sina.com.cn/rss/",
        "type": "rss"
    }

    # 所有来源映射
    ALL_SOURCES = {
        # 原有来源
        "huxiu": HUXIU,
        "36kr": KR36,
        "xueqiu": XUEQIU,
        "cls": CLS,
        "eastmoney": EASTMONEY,
        "yicai": YICAI,
        "stcn": STCN,
        "jiemian": JIEMIAN,
        "caixin": CAIXIN,
        "wallstreetcn": WALLSTREETCN,
        "jin10": JIN10,
        "tonghuashun": TONGHUASHUN,
        # 新增RSS来源
        "ftchinese": FTCHINESE,
        "wsjcn": WSJCN,
        "netease_money": NETEASE_MONEY,
        "tmtpost": TMTPOST,
        "iyiou": IYIOU,
        "ifanr": IFANR,
        "xinhua08": XINHUA08,
        "investing": INVESTING,
        "chinanews": CHINANEWS,
        "sina_finance": SINA_FINANCE,
    }


# ==================== 日期工具 ====================

class DateFilter:
    """日期过滤器"""

    def __init__(self, days: int = 2):
        """
        初始化日期过滤器

        Args:
            days: 包含今天在内的近X天 (默认2天 = 昨天和今天)
        """
        self.days = days
        self.now = datetime.now()
        self.cutoff_date = self.now - timedelta(days=days - 1)
        # 设置为当天开始时间
        self.cutoff_date = self.cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """解析各种格式的日期字符串"""
        if not date_str:
            return None

        # 常见日期格式列表
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
            "%a, %d %b %Y %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                # 处理时区后缀
                clean_str = date_str.replace('Z', '+00:00') if 'Z' in date_str else date_str
                # 处理 +0800 格式
                clean_str = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', clean_str)
                return datetime.strptime(clean_str[:len(datetime.now().strftime(fmt.replace('%z', '')))], fmt.replace('%z', ''))
            except (ValueError, TypeError):
                continue

        # 尝试解析时间戳
        try:
            ts = int(date_str)
            if ts > 1000000000000:
                ts = ts / 1000
            return datetime.fromtimestamp(ts)
        except (ValueError, TypeError):
            pass

        return None

    def is_within_range(self, date_str: str) -> bool:
        """检查日期是否在指定范围内"""
        parsed_date = self.parse_date(date_str)
        if parsed_date is None:
            # 如果无法解析日期，默认保留（可能是最新新闻）
            return True
        return parsed_date >= self.cutoff_date

    def get_date_range_str(self) -> str:
        """获取日期范围描述"""
        start = self.cutoff_date.strftime('%Y-%m-%d')
        end = self.now.strftime('%Y-%m-%d')
        return f"{start} 至 {end}"


# ==================== 新闻抓取器 ====================

class FinancialNewsFetcher:
    """金融新闻抓取器 - 支持多数据源"""

    def __init__(self, output_base_dir: str = ".", days: int = 2):
        # 创建带时间戳的输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(output_base_dir) / f"news_output_{timestamp}"
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # 日期过滤器
        self.date_filter = DateFilter(days=days)

        # 请求头，模拟浏览器
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/",
        }

        # 存储抓取的新闻
        self.news_cache: List[Dict] = []
        # 统计各来源抓取情况
        self.fetch_stats: Dict[str, Dict] = {}

    @staticmethod
    def clean_html(text: str) -> str:
        """清理HTML标签，提取纯文本"""
        if not text:
            return ""

        # 解码HTML实体
        text = html.unescape(text)

        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊字符
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&[a-z]+;', '', text)

        return text.strip()

    @staticmethod
    def contains_chinese_company(title: str) -> tuple:
        """
        检查标题是否包含中国知名公司名
        返回: (是否包含, 公司名)
        """
        if not title:
            return False, None

        for company in FAMOUS_CHINESE_COMPANIES:
            if company in title:
                return True, company

        return False, None

    # ==================== Scrapling 增强抓取 ====================

    def _fetch_with_scrapling(self, url: str, source_name: str = "") -> Optional[str]:
        """
        使用 Scrapling 的 StealthyFetcher 抓取难爬的页面
        绕过 Cloudflare、Turnstile 等反爬机制
        """
        if not HAS_SCRAPLING:
            return None

        try:
            print(f"   🕷️  使用 Scrapling 绕过反爬 ({source_name})...")
            # 使用 StealthyFetcher 绕过反爬
            StealthyFetcher.adaptive = True
            response = StealthyFetcher.fetch(url, headless=True, network_idle=True)
            return response.text
        except Exception as e:
            print(f"   ⚠️  Scrapling 抓取失败: {e}")
            return None

    def _fetch_with_dynamic(self, url: str) -> Optional[str]:
        """
        使用 DynamicFetcher 抓取 JavaScript 渲染的页面
        适用于 SPA 网站
        """
        if not HAS_SCRAPLING:
            return None

        try:
            print(f"   🔄 使用 DynamicFetcher 渲染 JS...")
            response = DynamicFetcher.fetch(url, wait_for_selector=".content", timeout=30)
            return response.text
        except Exception as e:
            print(f"   ⚠️  DynamicFetcher 抓取失败: {e}")
            return None

    # ==================== RSS 源抓取 ====================

    def _fetch_rss(self, source_key: str) -> List[Dict]:
        """通用RSS抓取方法"""
        source = NewsSource.ALL_SOURCES.get(source_key)
        if not source or source["type"] != "rss":
            return []

        if not HAS_FEEDPARSER:
            print(f"   ⚠️  {source['name']}: 需要安装 feedparser")
            return []

        print(f"📰 正在抓取 {source['name']}...")
        news_list = []

        try:
            feed = feedparser.parse(source["rss_url"])

            for entry in feed.entries[:30]:  # 取前30条
                published = entry.get("published", "") or entry.get("pubDate", "") or entry.get("updated", "")

                # 日期过滤
                if not self.date_filter.is_within_range(published):
                    continue

                title = entry.get("title", "")

                # 检查标题是否包含中国知名公司
                has_company, company_name = self.contains_chinese_company(title)
                if not has_company:
                    continue

                # 清理HTML标签
                summary_raw = entry.get("summary", "") or entry.get("description", "")
                content_raw = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""

                news = {
                    "source": source["name"],
                    "title": title,
                    "company": company_name,
                    "link": entry.get("link", ""),
                    "summary": self.clean_html(summary_raw),
                    "published": published,
                    "content": self.clean_html(content_raw)
                }
                news_list.append(news)

            print(f"   ✅ {source['name']}: {len(news_list)} 条")
            self.fetch_stats[source_key] = {"status": "success", "count": len(news_list)}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            self.fetch_stats[source_key] = {"status": "failed", "error": str(e)}

        return news_list

    # ==================== API 源抓取 ====================

    def fetch_36kr_api(self) -> List[Dict]:
        """抓取36氪快讯API (新版)"""
        source = NewsSource.KR36
        print(f"📰 正在抓取 {source['name']}...")
        news_list = []

        try:
            # 使用新的API地址
            url = "https://36kr.com/api/newsflash"
            params = {"page": 1, "page_size": 30}
            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                items = result.get("data", {}).get("items", [])

                for item in items[:30]:
                    # 36kr API返回的时间戳是毫秒
                    published_ts = item.get("published_at", "") or item.get("created_at", "")
                    if published_ts:
                        published = str(published_ts)
                    else:
                        published = ""

                    # 日期过滤
                    if published and not self.date_filter.is_within_range(published):
                        continue

                    title = item.get("title", "") or (item.get("description", "")[:80] if item.get("description") else "")

                    # 检查标题是否包含中国知名公司
                    has_company, company_name = self.contains_chinese_company(title)
                    if not has_company:
                        continue

                    news = {
                        "source": source["name"],
                        "title": title,
                        "company": company_name,
                        "link": f"https://36kr.com/newsflashes/{item.get('id', '')}",
                        "summary": self.clean_html(item.get("description", "")),
                        "published": published,
                        "content": self.clean_html(item.get("content", ""))
                    }
                    news_list.append(news)

                print(f"   ✅ {source['name']}: {len(news_list)} 条")
                self.fetch_stats["36kr"] = {"status": "success", "count": len(news_list)}
            else:
                print(f"   ❌ {source['name']}: HTTP {response.status_code}")
                self.fetch_stats["36kr"] = {"status": "failed", "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            self.fetch_stats["36kr"] = {"status": "failed", "error": str(e)}

        return news_list

    def fetch_xueqiu_api(self) -> List[Dict]:
        """抓取雪球热榜API（带 Scrapling fallback）"""
        source = NewsSource.XUEQIU
        print(f"📰 正在抓取 {source['name']}...")
        news_list = []

        try:
            url = "https://xueqiu.com/statuses/hot/listV2.json?since_id=-1&max_id=-1&size=30"
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code == 200:
                result = response.json()
                items = result.get("items", [])

                for item in items[:20]:
                    original = item.get("original_status", {})
                    created_at = original.get("created_at", 0)

                    if created_at and not self.date_filter.is_within_range(str(created_at)):
                        continue

                    title = original.get("title", "") or original.get("text", "")[:100]

                    # 检查标题是否包含中国知名公司
                    has_company, company_name = self.contains_chinese_company(title)
                    if not has_company:
                        continue

                    news = {
                        "source": source["name"],
                        "title": title,
                        "company": company_name,
                        "link": f"https://xueqiu.com/{original.get('user', {}).get('id', '')}/{original.get('id', '')}",
                        "summary": self.clean_html(original.get("text", "")),
                        "published": str(created_at),
                        "content": ""
                    }
                    news_list.append(news)

                print(f"   ✅ {source['name']}: {len(news_list)} 条")
                self.fetch_stats["xueqiu"] = {"status": "success", "count": len(news_list)}
            else:
                # 如果普通请求失败，尝试使用 Scrapling
                print(f"   ⚠️  普通请求失败 (HTTP {response.status_code})，尝试 Scrapling...")
                html_content = self._fetch_with_scrapling("https://xueqiu.com/hq", "雪球")
                if html_content:
                    # 解析 HTML 内容（简化版）
                    print(f"   🔄 使用 Scrapling 成功获取雪球页面")
                    # 注意：HTML 解析需要根据实际页面结构调整
                    # 这里暂不展开，留作后续优化
                self.fetch_stats["xueqiu"] = {"status": "failed", "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            # 尝试 Scrapling fallback
            print(f"   🔄 尝试使用 Scrapling 作为备用方案...")
            html_content = self._fetch_with_scrapling("https://xueqiu.com/hq", "雪球")
            if html_content:
                print(f"   ✅ Scrapling 备用方案成功")
            self.fetch_stats["xueqiu"] = {"status": "failed", "error": str(e)}

        return news_list

    def fetch_cls_api(self) -> List[Dict]:
        """抓取财联社电报API"""
        source = NewsSource.CLS
        print(f"📰 正在抓取 {source['name']}...")
        news_list = []

        try:
            url = "https://www.cls.cn/nodeapi/telegraphs"
            params = {"rn": 30, "refresh_type": 1}
            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                items = result.get("data", {}).get("roll_data", [])

                for item in items[:25]:
                    published = str(item.get("ctime", ""))

                    if not self.date_filter.is_within_range(published):
                        continue

                    title = item.get("title", "")

                    # 检查标题是否包含中国知名公司
                    has_company, company_name = self.contains_chinese_company(title)
                    if not has_company:
                        continue

                    news = {
                        "source": source["name"],
                        "title": title,
                        "company": company_name,
                        "link": f"https://www.cls.cn/detail/{item.get('id', '')}",
                        "summary": self.clean_html(item.get("content", "")),
                        "published": published,
                        "content": self.clean_html(item.get("content", ""))
                    }
                    news_list.append(news)

                print(f"   ✅ {source['name']}: {len(news_list)} 条")
                self.fetch_stats["cls"] = {"status": "success", "count": len(news_list)}
            else:
                print(f"   ❌ {source['name']}: HTTP {response.status_code}")
                self.fetch_stats["cls"] = {"status": "failed", "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            self.fetch_stats["cls"] = {"status": "failed", "error": str(e)}

        return news_list

    def fetch_eastmoney_api(self) -> List[Dict]:
        """抓取东方财富快讯API"""
        source = NewsSource.EASTMONEY
        print(f"📰 正在抓取 {source['name']}...")
        news_list = []

        try:
            url = "https://np-listapi.eastmoney.com/comm/web/getFastNewsList"
            params = {
                "client": "web",
                "biz": "web_724",
                "fastColumn": "102",
                "sortEnd": "",
                "pageSize": 30
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                items = result.get("data", {}).get("fastChannelList", [])

                for item in items[:25]:
                    published = str(item.get("showTime", ""))

                    if not self.date_filter.is_within_range(published):
                        continue

                    title = item.get("title", "")

                    # 检查标题是否包含中国知名公司
                    has_company, company_name = self.contains_chinese_company(title)
                    if not has_company:
                        continue

                    news = {
                        "source": source["name"],
                        "title": title,
                        "company": company_name,
                        "link": item.get("url", ""),
                        "summary": self.clean_html(item.get("summary", "") or item.get("title", "")),
                        "published": published,
                        "content": ""
                    }
                    news_list.append(news)

                print(f"   ✅ {source['name']}: {len(news_list)} 条")
                self.fetch_stats["eastmoney"] = {"status": "success", "count": len(news_list)}
            else:
                print(f"   ❌ {source['name']}: HTTP {response.status_code}")
                self.fetch_stats["eastmoney"] = {"status": "failed", "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            self.fetch_stats["eastmoney"] = {"status": "failed", "error": str(e)}

        return news_list

    def fetch_wallstreetcn_api(self) -> List[Dict]:
        """抓取华尔街见闻API"""
        source = NewsSource.WALLSTREETCN
        print(f"📰 正在抓取 {source['name']}...")
        news_list = []

        try:
            url = "https://api-one.wallstreetcn.com/apiv1/content/articles"
            params = {"channel": "global-channel", "limit": 30}
            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                items = result.get("data", {}).get("items", [])

                for item in items[:25]:
                    published = str(item.get("display_time", ""))

                    if not self.date_filter.is_within_range(published):
                        continue

                    title = item.get("title", "")

                    # 检查标题是否包含中国知名公司
                    has_company, company_name = self.contains_chinese_company(title)
                    if not has_company:
                        continue

                    news = {
                        "source": source["name"],
                        "title": title,
                        "company": company_name,
                        "link": f"https://wallstreetcn.com/articles/{item.get('id', '')}",
                        "summary": self.clean_html(item.get("content_text", "") or item.get("description", "")),
                        "published": published,
                        "content": self.clean_html(item.get("content", ""))
                    }
                    news_list.append(news)

                print(f"   ✅ {source['name']}: {len(news_list)} 条")
                self.fetch_stats["wallstreetcn"] = {"status": "success", "count": len(news_list)}
            else:
                print(f"   ❌ {source['name']}: HTTP {response.status_code}")
                self.fetch_stats["wallstreetcn"] = {"status": "failed", "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            self.fetch_stats["wallstreetcn"] = {"status": "failed", "error": str(e)}

        return news_list

    def fetch_jin10_api(self) -> List[Dict]:
        """抓取金十数据快讯API"""
        source = NewsSource.JIN10
        print(f"📰 正在抓取 {source['name']}...")
        news_list = []

        try:
            url = "https://flash-api.jin10.com/get_flash_list"
            params = {"channel": "-8200", "vip": 1, "max_time": ""}
            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                items = result.get("data", [])

                for item in items[:30]:
                    published = str(item.get("time", ""))

                    if not self.date_filter.is_within_range(published):
                        continue

                    title = item.get("data", {}).get("title", "") or item.get("data", {}).get("content", "")[:80]

                    # 检查标题是否包含中国知名公司
                    has_company, company_name = self.contains_chinese_company(title)
                    if not has_company:
                        continue

                    news = {
                        "source": source["name"],
                        "title": title,
                        "company": company_name,
                        "link": f"https://www.jin10.com/flash/{item.get('id', '')}.html",
                        "summary": self.clean_html(item.get("data", {}).get("content", "")),
                        "published": published,
                        "content": ""
                    }
                    news_list.append(news)

                print(f"   ✅ {source['name']}: {len(news_list)} 条")
                self.fetch_stats["jin10"] = {"status": "success", "count": len(news_list)}
            else:
                print(f"   ❌ {source['name']}: HTTP {response.status_code}")
                self.fetch_stats["jin10"] = {"status": "failed", "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            self.fetch_stats["jin10"] = {"status": "failed", "error": str(e)}

        return news_list

    # ==================== 统一抓取入口 ====================

    def fetch_all_sources(self, sources: List[str] = None) -> List[Dict]:
        """抓取所有新闻源"""
        if sources is None:
            # 默认抓取所有源
            sources = list(NewsSource.ALL_SOURCES.keys())

        all_news = []
        self.fetch_stats = {}

        print(f"\n📅 日期范围: {self.date_filter.get_date_range_str()} (近 {self.date_filter.days} 天)")
        print("-" * 50)

        # RSS 源 - 包含原有的和新增的
        rss_sources = [
            # 原有RSS源
            "huxiu", "yicai", "stcn", "jiemian", "caixin",
            # 新增RSS源
            "ftchinese", "wsjcn", "netease_money", "tmtpost",
            "iyiou", "ifanr", "xinhua08", "investing",
            "chinanews", "sina_finance"
        ]
        for source_key in rss_sources:
            if source_key in sources:
                all_news.extend(self._fetch_rss(source_key))

        # API 源
        api_sources = {
            "36kr": self.fetch_36kr_api,
            "xueqiu": self.fetch_xueqiu_api,
            "cls": self.fetch_cls_api,
            "eastmoney": self.fetch_eastmoney_api,
            "wallstreetcn": self.fetch_wallstreetcn_api,
            "jin10": self.fetch_jin10_api,
        }

        for source_key, fetch_func in api_sources.items():
            if source_key in sources:
                all_news.extend(fetch_func())

        # 去重（基于标题）
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title = news.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)

        self.news_cache = unique_news
        return unique_news

    # ==================== 筛选与保存 ====================

    def filter_financial_news(self, keywords: List[str] = None) -> List[Dict]:
        """筛选金融相关新闻（已在抓取时过滤公司名，这里主要做相关度计算）"""
        if keywords is None:
            keywords = [
                "股票", "A股", "基金", "投资", "理财", "金融", "银行",
                "证券", "经济", "财报", "IPO", "上市", "融资", "并购",
                "利率", "央行", "政策", "监管", "行业", "科技", "消费",
                "新能源", "芯片", "医药", "互联网", "电商", "AI", "人工智能",
                "汽车", "电动车", "半导体", "房地产", "保险", "外汇", "黄金"
            ]

        filtered = []
        for news in self.news_cache:
            title = news.get("title", "")
            summary = news.get("summary", "")
            content = title + " " + summary

            # 计算相关度
            relevance = sum(1 for kw in keywords if kw in content)
            news["relevance"] = max(relevance, 1)  # 至少为1
            filtered.append(news)

        # 按相关度排序
        filtered.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return filtered

    def save_news(self, news_list: List[Dict], filename: str = None) -> str:
        """保存新闻到JSON文件"""
        if filename is None:
            filename = "news_result.json"

        filepath = self.output_dir / filename

        # 按来源分组统计
        by_source = {}
        for news in news_list:
            source = news.get("source", "未知")
            by_source[source] = by_source.get(source, 0) + 1

        # 按公司分组统计
        by_company = {}
        for news in news_list:
            company = news.get("company", "未知")
            by_company[company] = by_company.get(company, 0) + 1

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "fetch_time": datetime.now().isoformat(),
                "date_range": self.date_filter.get_date_range_str(),
                "days": self.date_filter.days,
                "total_count": len(news_list),
                "by_source": by_source,
                "by_company": by_company,
                "fetch_stats": self.fetch_stats,
                "news": news_list
            }, f, ensure_ascii=False, indent=2)

        print(f"💾 新闻已保存到: {filepath}")
        return str(filepath)


# ==================== 内容分析器 ====================

class ContentAnalyzer:
    """内容分析器 - 生成小红书风格的财经分析文稿"""

    def __init__(self, output_dir: str = "./news_output"):
        self.output_dir = Path(output_dir)
        # 不再自动创建目录，因为 FinancialNewsFetcher 已经创建了

    def generate_xiaohongshu_draft(
        self,
        news: Dict,
        style: str = "专业分析",
        include_investment_tips: bool = True
    ) -> Dict:
        """生成小红书风格的分析文稿"""

        title = news.get("title", "")
        summary = news.get("summary", "")
        source = news.get("source", "")

        draft = {
            "original_news": news,
            "style": style,
            "generated_at": datetime.now().isoformat(),
            "xiaohongshu_title": self._generate_catchy_title(title),
            "content": {
                "hook": "",
                "background": "",
                "analysis": "",
                "impact": "",
                "investment_view": "",
                "action_items": [],
            },
            "tags": [],
            "hashtags": [],
            "image_prompts": [],
            "related_stocks": [],
            "related_sectors": [],
        }

        return draft

    def _generate_catchy_title(self, original_title: str) -> str:
        """生成吸引眼球的小红书标题"""
        templates = [
            "🔥重磅！{title}",
            "💰投资必看｜{title}",
            "📊{title}，对A股有什么影响？",
            "⚠️紧急关注！{title}",
            "🚀{title}，这些板块要起飞？",
        ]

        import random
        return random.choice(templates).format(title=original_title[:20])

    def create_analysis_prompt(self, news: Dict) -> str:
        """创建用于 Claude 分析的 Prompt"""

        prompt = f"""
# 任务：金融新闻深度分析

请分析以下财经新闻，并生成小红书风格的财经分析文稿。

## 原始新闻
- **标题**: {news.get('title', '')}
- **来源**: {news.get('source', '')}
- **摘要**: {news.get('summary', '')}
- **链接**: {news.get('link', '')}

## 分析要求

### 1. 标题优化
生成一个吸引眼球的小红书标题（不超过25字），要求：
- 使用数字或疑问句
- 适当使用表情符号
- 突出投资机会或风险

### 2. 内容分析
请从以下维度分析：

**a) 事件背景** (50-100字)
- 这条新闻的核心事件是什么？
- 发生的背景和原因？

**b) 深度解读** (100-200字)
- 这件事的本质是什么？
- 有哪些深层次的逻辑？
- 对市场/行业意味着什么？

**c) 影响分析**
- 受益行业/板块：
- 受损行业/板块：
- 相关A股上市公司（列举3-5家）：

**d) 投资观点** (50-100字)
- 短期影响？
- 中长期趋势？
- 投资者应该如何应对？

### 3. 小红书元素
- **标签**: 5-8个相关标签
- **Hashtag**: 3-5个热门话题标签

### 4. 图片提示词
生成2-3个配图的 AI 绘画提示词（用于 Midjourney/Stable Diffusion）
- 封面图提示词
- 内容配图提示词

---

请以 JSON 格式输出结果。
"""
        return prompt

    def save_draft(self, draft: Dict, filename: str = None) -> str:
        """保存文稿"""
        if filename is None:
            filename = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)

        print(f"💾 文稿已保存到: {filepath}")
        return str(filepath)


# ==================== 主函数 ====================

def main():
    """主函数"""

    parser = argparse.ArgumentParser(description="金融新闻自动化工作流")
    parser.add_argument(
        "--days",
        type=int,
        default=2,
        help="抓取近X天的新闻 (默认2天 = 昨天和今天)"
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="all",
        help="新闻来源，用逗号分隔 (默认all，可选: huxiu,36kr,xueqiu,cls,eastmoney,yicai,stcn,jiemian,caixin,wallstreetcn,jin10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="输出基础目录 (默认当前目录，会自动创建 news_output_日期_时间 子目录)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 金融新闻自动化工作流 - 新闻抓取与分析")
    print("=" * 60)
    print()

    # 确定要抓取的源
    if args.sources.lower() == "all":
        sources = list(NewsSource.ALL_SOURCES.keys())
    else:
        sources = [s.strip() for s in args.sources.split(",")]

    print(f"📋 新闻来源: {', '.join(sources)}")
    print(f"🏢 筛选条件: 标题必须包含中国知名公司名")
    print()

    # 1. 抓取新闻
    print("【步骤1】抓取财经新闻...")
    print("-" * 40)

    fetcher = FinancialNewsFetcher(output_base_dir=args.output, days=args.days)
    print(f"📂 输出目录: {fetcher.output_dir}")
    print()

    all_news = fetcher.fetch_all_sources(sources=sources)

    if not all_news:
        print("❌ 没有抓取到符合条件的新闻（标题需包含中国知名公司名）")
        return

    print(f"\n📊 共抓取 {len(all_news)} 条新闻")

    # 显示抓取统计
    print("\n📈 各来源统计:")
    for source, stats in fetcher.fetch_stats.items():
        status_icon = "✅" if stats["status"] == "success" else "❌"
        count = stats.get("count", 0)
        print(f"   {status_icon} {source}: {count} 条")

    # 2. 筛选金融相关新闻（计算相关度）
    print("\n【步骤2】计算新闻相关度...")
    print("-" * 40)

    financial_news = fetcher.filter_financial_news()
    print(f"📊 共 {len(financial_news)} 条新闻")

    # 按公司分组显示
    by_company = {}
    for news in financial_news:
        company = news.get("company", "未知")
        if company not in by_company:
            by_company[company] = []
        by_company[company].append(news)

    print("\n🏢 按公司分组:")
    for company, news_list in sorted(by_company.items(), key=lambda x: -len(x[1])):
        print(f"   {company}: {len(news_list)} 条")

    # 显示前10条
    print("\n🔥 Top 10 热点新闻:")
    for i, news in enumerate(financial_news[:10], 1):
        title = news['title'][:45] + "..." if len(news['title']) > 45 else news['title']
        company = news.get('company', '')
        print(f"\n{i}. 【{news['source']}】【{company}】{title}")
        print(f"   相关度: {'⭐' * min(news.get('relevance', 1), 5)}")

    # 3. 保存新闻
    print("\n【步骤3】保存新闻数据...")
    print("-" * 40)

    news_file = fetcher.save_news(financial_news)

    # 4. 生成分析文稿模板
    print("\n【步骤4】生成分析提示词...")
    print("-" * 40)

    analyzer = ContentAnalyzer(output_dir=str(fetcher.output_dir))

    if financial_news:
        top_news = financial_news[0]
        analysis_prompt = analyzer.create_analysis_prompt(top_news)

        prompt_file = fetcher.output_dir / "prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(analysis_prompt)

        print(f"📝 分析提示词已保存到: {prompt_file}")

    print("\n" + "=" * 60)
    print("✅ 工作流完成！")
    print("=" * 60)
    print(f"\n📂 输出目录: {fetcher.output_dir}")
    print(f"📄 新闻文件: {news_file}")
    print("\n🎯 下一步:")
    print("   1. 查看保存的新闻JSON文件")
    print("   2. 使用 Claude 分析生成的提示词")
    print("   3. 生成配图并发布到小红书")


if __name__ == "__main__":
    main()
