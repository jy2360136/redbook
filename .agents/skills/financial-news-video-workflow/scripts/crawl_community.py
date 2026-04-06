"""
社区论坛信息抓取工具
====================
功能：从雪球、知乎等社区论坛抓取用户评论和讨论，用于舆情分析

支持的社区：
- 雪球网 (xueqiu.com)
- 知乎 (zhihu.com)

使用场景：
1. 根据已确定的公司选题，在社区中搜索相关讨论
2. 收集用户真实评价和细碎信息
3. 分析舆情趋势和用户观点
"""

import sys
import io
import re
import argparse
import html
import asyncio

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import os
from datetime import datetime
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

# 尝试导入 Crawl4AI
try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy, AsyncHTTPCrawlerStrategy
    HAS_CRAWL4AI = True
    print("✅ Crawl4AI 已安装，增强抓取功能已启用")
except ImportError:
    HAS_CRAWL4AI = False
    print("⚠️  Crawl4AI 未安装，将使用传统抓取方式。运行: pip install crawl4ai")


# ==================== 社区配置 ====================

class CommunitySource:
    """社区论坛配置"""

    XUEQIU = {
        "name": "雪球网",
        "base_url": "https://www.xueqiu.com",
        "search_url": "https://xueqiu.com/k?q={keyword}",
        "type": "community"
    }

    ZHIHU = {
        "name": "知乎",
        "base_url": "https://www.zhihu.com",
        "search_url": "https://www.zhihu.com/search?type=content&q={keyword}",
        "type": "community"
    }

    # 所有来源映射
    ALL_SOURCES = {
        "xueqiu": XUEQIU,
        "zhihu": ZHIHU,
    }


# ==================== 社区抓取器 ====================

class CommunityCrawler:
    """社区论坛抓取器"""

    def __init__(self, output_base_dir: str = "."):
        # 创建带时间戳的输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(output_base_dir) / f"community_output_{timestamp}"
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # 请求头，模拟浏览器
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/",
        }

        # 存储抓取的评论
        self.comments_cache: List[Dict] = []
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

    # ==================== Crawl4AI 增强抓取 ====================

    async def _fetch_with_crawl4ai_async(self, url: str, source_name: str = "") -> Optional[str]:
        """
        使用 Crawl4AI 抓取网页内容
        支持复杂的网页结构和反爬机制
        """
        if not HAS_CRAWL4AI:
            return None

        try:
            print(f"   🕷️  使用 Crawl4AI (Playwright) 抓取 ({source_name})...")
            # 使用 Playwright 爬虫策略，利用已安装的 Chromium 浏览器
            crawler = AsyncWebCrawler(crawler_strategy=AsyncPlaywrightCrawlerStrategy())
            results = await crawler.arun(
                url=url,
                max_depth=1,
                max_pages=1,
                timeout=30,  # 增加超时时间
                headless=True  # 使用无头模式
            )
            
            if results and len(results) > 0:
                result = results[0]
                if hasattr(result, 'html'):
                    return result.html
            return None
        except Exception as e:
            print(f"   ⚠️  Crawl4AI 抓取失败: {e}")
            # 如果 Playwright 失败，尝试使用 HTTP 策略作为备用
            try:
                print(f"   🔄 尝试使用 HTTP 策略作为备用...")
                crawler = AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy())
                results = await crawler.arun(
                    url=url,
                    max_depth=1,
                    max_pages=1
                )
                if results and len(results) > 0:
                    result = results[0]
                    if hasattr(result, 'html'):
                        return result.html
            except Exception as http_error:
                print(f"   ⚠️  HTTP 策略也失败: {http_error}")
            return None

    def _fetch_with_crawl4ai(self, url: str, source_name: str = "") -> Optional[str]:
        """
        同步版本的 Crawl4AI 抓取
        """
        return asyncio.run(self._fetch_with_crawl4ai_async(url, source_name))

    # ==================== 传统 HTTP 抓取 ====================

    def _fetch_with_requests(self, url: str, source_name: str = "") -> Optional[str]:
        """
        使用传统的 requests 库抓取网页
        """
        try:
            print(f"   🌐 使用 requests 抓取 ({source_name})...")
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                return response.text
            else:
                print(f"   ⚠️  HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"   ⚠️  requests 抓取失败: {e}")
            return None

    # ==================== 雪球网抓取 ====================

    async def fetch_xueqiu_comments(self, keyword: str) -> List[Dict]:
        """抓取雪球网相关评论"""
        source = CommunitySource.XUEQIU
        print(f"📰 正在抓取 {source['name']} 关于 '{keyword}' 的讨论...")
        comments_list = []

        try:
            # 构建搜索URL
            search_url = source["search_url"].format(keyword=keyword)
            print(f"   🔍 访问雪球搜索页面: {search_url}")
            
            # 使用 Crawl4AI 抓取
            html_content = await self._fetch_with_crawl4ai_async(search_url, "雪球搜索")
            
            if html_content:
                print(f"   ✅ 成功获取雪球搜索页面")
                # 解析搜索结果
                if HAS_BS4:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 尝试不同的选择器查找帖子
                    # 雪球的页面结构可能会变化，尝试多种选择器
                    post_selectors = [
                        '.search-result-item',
                        '.article-item',
                        '.list-item',
                        'div[class*="item"]'
                    ]
                    
                    posts = []
                    for selector in post_selectors:
                        found_posts = soup.select(selector)
                        if found_posts:
                            posts = found_posts
                            break
                    
                    if posts:
                        print(f"   📝 找到 {len(posts)} 个相关帖子")
                        
                        # 解析前10个帖子
                        for i, post in enumerate(posts[:10]):
                            # 尝试提取标题
                            title_elem = post.select_one('a.title') or post.select_one('h3') or post.select_one('h2')
                            title = title_elem.text.strip() if title_elem else ""
                            
                            # 尝试提取链接
                            link_elem = post.select_one('a[href]')
                            link = link_elem['href'] if link_elem else ""
                            if link and not link.startswith('http'):
                                link = source["base_url"] + link
                            
                            # 尝试提取内容
                            content_elem = post.select_one('.content') or post.select_one('.desc') or post.select_one('.text')
                            content = content_elem.text.strip() if content_elem else ""
                            
                            # 尝试提取作者
                            author_elem = post.select_one('.user-name') or post.select_one('.author')
                            author = author_elem.text.strip() if author_elem else ""
                            
                            # 尝试提取发布时间
                            time_elem = post.select_one('.time') or post.select_one('.date')
                            time_str = time_elem.text.strip() if time_elem else ""
                            
                            # 尝试提取点赞数
                            like_elem = post.select_one('.like-count') or post.select_one('.likes')
                            like_count = like_elem.text.strip() if like_elem else "0"
                            
                            # 尝试提取评论数
                            comment_elem = post.select_one('.comment-count') or post.select_one('.comments')
                            comment_count = comment_elem.text.strip() if comment_elem else "0"
                            
                            # 构建评论对象
                            comment = {
                                "source": source["name"],
                                "keyword": keyword,
                                "title": title,
                                "content": self.clean_html(content),
                                "link": link,
                                "author": author,
                                "time": time_str,
                                "like_count": like_count,
                                "comment_count": comment_count,
                                "fetched_at": datetime.now().isoformat()
                            }
                            comments_list.append(comment)
                            print(f"   ✅ 提取帖子 {i+1}: {title[:50]}...")
                    else:
                        print(f"   ⚠️  未找到搜索结果帖子")
                else:
                    print(f"   ⚠️  BeautifulSoup 未安装，无法解析HTML")
            else:
                print(f"   ❌ 无法获取雪球搜索页面")
            
            if comments_list:
                print(f"   ✅ {source['name']}: {len(comments_list)} 条评论")
                self.fetch_stats["xueqiu"] = {"status": "success", "count": len(comments_list)}
            else:
                print(f"   ⚠️  {source['name']}: 未抓取到相关评论")
                self.fetch_stats["xueqiu"] = {"status": "failed", "error": "未抓取到相关评论"}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            self.fetch_stats["xueqiu"] = {"status": "failed", "error": str(e)}

        return comments_list

    # ==================== 知乎抓取 ====================

    async def fetch_zhihu_comments(self, keyword: str) -> List[Dict]:
        """抓取知乎相关评论"""
        source = CommunitySource.ZHIHU
        print(f"📰 正在抓取 {source['name']} 关于 '{keyword}' 的讨论...")
        comments_list = []

        try:
            # 构建搜索URL
            search_url = source["search_url"].format(keyword=keyword)
            print(f"   🔍 访问知乎搜索页面: {search_url}")
            
            # 使用 Crawl4AI 抓取
            html_content = await self._fetch_with_crawl4ai_async(search_url, "知乎搜索")
            
            if html_content:
                print(f"   ✅ 成功获取知乎搜索页面")
                # 解析搜索结果
                if HAS_BS4:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 尝试不同的选择器查找问题和回答
                    # 知乎的页面结构可能会变化，尝试多种选择器
                    item_selectors = [
                        '.List-item',
                        '.search-result-item',
                        '.ContentItem',
                        'div[class*="item"]'
                    ]
                    
                    items = []
                    for selector in item_selectors:
                        found_items = soup.select(selector)
                        if found_items:
                            items = found_items
                            break
                    
                    if items:
                        print(f"   📝 找到 {len(items)} 个相关内容")
                        
                        # 解析前10个内容
                        for i, item in enumerate(items[:10]):
                            # 尝试提取标题
                            title_elem = item.select_one('.ContentItem-title') or item.select_one('h2') or item.select_one('.title')
                            title = title_elem.text.strip() if title_elem else ""
                            
                            # 尝试提取链接
                            link_elem = item.select_one('a[href]')
                            link = link_elem['href'] if link_elem else ""
                            if link and not link.startswith('http'):
                                link = source["base_url"] + link
                            
                            # 尝试提取内容
                            content_elem = item.select_one('.RichText') or item.select_one('.content') or item.select_one('.excerpt')
                            content = content_elem.text.strip() if content_elem else ""
                            
                            # 尝试提取作者
                            author_elem = item.select_one('.UserLink') or item.select_one('.author')
                            author = author_elem.text.strip() if author_elem else ""
                            
                            # 尝试提取发布时间
                            time_elem = item.select_one('.ContentItem-time') or item.select_one('.time')
                            time_str = time_elem.text.strip() if time_elem else ""
                            
                            # 尝试提取点赞数
                            like_elem = item.select_one('.VoteButton--up') or item.select_one('.likes')
                            like_count = like_elem.text.strip() if like_elem else "0"
                            
                            # 尝试提取评论数
                            comment_elem = item.select_one('.CommentCount') or item.select_one('.comments')
                            comment_count = comment_elem.text.strip() if comment_elem else "0"
                            
                            # 构建评论对象
                            comment = {
                                "source": source["name"],
                                "keyword": keyword,
                                "title": title,
                                "content": self.clean_html(content),
                                "link": link,
                                "author": author,
                                "time": time_str,
                                "like_count": like_count,
                                "comment_count": comment_count,
                                "fetched_at": datetime.now().isoformat()
                            }
                            comments_list.append(comment)
                            print(f"   ✅ 提取内容 {i+1}: {title[:50]}...")
                    else:
                        print(f"   ⚠️  未找到搜索结果内容")
                else:
                    print(f"   ⚠️  BeautifulSoup 未安装，无法解析HTML")
            else:
                print(f"   ❌ 无法获取知乎搜索页面")
            
            if comments_list:
                print(f"   ✅ {source['name']}: {len(comments_list)} 条评论")
                self.fetch_stats["zhihu"] = {"status": "success", "count": len(comments_list)}
            else:
                print(f"   ⚠️  {source['name']}: 未抓取到相关评论")
                self.fetch_stats["zhihu"] = {"status": "failed", "error": "未抓取到相关评论"}

        except Exception as e:
            print(f"   ❌ {source['name']}: {e}")
            self.fetch_stats["zhihu"] = {"status": "failed", "error": str(e)}

        return comments_list

    # ==================== 统一抓取入口 ====================

    async def fetch_all_communities(self, keyword: str, sources: List[str] = None) -> List[Dict]:
        """抓取所有社区论坛"""
        if sources is None:
            # 默认抓取所有源
            sources = list(CommunitySource.ALL_SOURCES.keys())

        all_comments = []
        self.fetch_stats = {}

        print(f"\n🔍 搜索关键词: {keyword}")
        print("-" * 50)

        # 抓取雪球网
        if "xueqiu" in sources:
            xueqiu_comments = await self.fetch_xueqiu_comments(keyword)
            all_comments.extend(xueqiu_comments)

        # 抓取知乎
        if "zhihu" in sources:
            zhihu_comments = await self.fetch_zhihu_comments(keyword)
            all_comments.extend(zhihu_comments)

        self.comments_cache = all_comments
        return all_comments

    def fetch_all_communities_sync(self, keyword: str, sources: List[str] = None) -> List[Dict]:
        """同步版本的抓取所有社区论坛"""
        return asyncio.run(self.fetch_all_communities(keyword, sources))

    # ==================== 分析与保存 ====================

    def analyze_sentiment(self, comments: List[Dict]) -> List[Dict]:
        """简单的情感分析"""
        # 这里可以实现更复杂的情感分析
        # 目前只是简单的关键词匹配
        positive_words = ["好", "棒", "优秀", "满意", "喜欢", "赞", "强", "牛", "厉害", "出色"]
        negative_words = ["差", "糟糕", "失望", "讨厌", "差", "弱", "垃圾", "烂", "坑", "差"]

        for comment in comments:
            content = comment.get("content", "")
            positive_count = sum(1 for word in positive_words if word in content)
            negative_count = sum(1 for word in negative_words if word in content)
            
            if positive_count > negative_count:
                comment["sentiment"] = "positive"
            elif negative_count > positive_count:
                comment["sentiment"] = "negative"
            else:
                comment["sentiment"] = "neutral"
            
            comment["sentiment_score"] = positive_count - negative_count

        return comments

    def save_comments(self, comments: List[Dict], keyword: str) -> str:
        """保存评论到JSON文件"""
        filename = f"comments_{keyword.replace(' ', '_')}.json"
        filepath = self.output_dir / filename

        # 按来源分组统计
        by_source = {}
        for comment in comments:
            source = comment.get("source", "未知")
            by_source[source] = by_source.get(source, 0) + 1

        # 按情感分组统计
        by_sentiment = {}
        for comment in comments:
            sentiment = comment.get("sentiment", "neutral")
            by_sentiment[sentiment] = by_sentiment.get(sentiment, 0) + 1

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "fetch_time": datetime.now().isoformat(),
                "keyword": keyword,
                "total_count": len(comments),
                "by_source": by_source,
                "by_sentiment": by_sentiment,
                "fetch_stats": self.fetch_stats,
                "comments": comments
            }, f, ensure_ascii=False, indent=2)

        print(f"💾 评论已保存到: {filepath}")
        return str(filepath)


# ==================== 主函数 ====================

async def main_async():
    """主函数"""

    parser = argparse.ArgumentParser(description="社区论坛信息抓取工具")
    parser.add_argument(
        "--keyword",
        type=str,
        required=True,
        help="搜索关键词（例如：小米汽车）"
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="all",
        help="社区来源，用逗号分隔 (默认all，可选: xueqiu,zhihu)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="输出基础目录 (默认当前目录，会自动创建 community_output_日期_时间 子目录)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 社区论坛信息抓取工具")
    print("=" * 60)
    print()

    # 确定要抓取的源
    if args.sources.lower() == "all":
        sources = list(CommunitySource.ALL_SOURCES.keys())
    else:
        sources = [s.strip() for s in args.sources.split(",")]

    print(f"📋 社区来源: {', '.join(sources)}")
    print(f"🔍 搜索关键词: {args.keyword}")
    print()

    # 1. 抓取评论
    print("【步骤1】抓取社区评论...")
    print("-" * 40)

    crawler = CommunityCrawler(output_base_dir=args.output)
    print(f"📂 输出目录: {crawler.output_dir}")
    print()

    all_comments = await crawler.fetch_all_communities(args.keyword, sources=sources)

    if not all_comments:
        print("❌ 没有抓取到相关评论")
        return

    print(f"\n📊 共抓取 {len(all_comments)} 条评论")

    # 显示抓取统计
    print("\n📈 各来源统计:")
    for source, stats in crawler.fetch_stats.items():
        status_icon = "✅" if stats["status"] == "success" else "❌"
        count = stats.get("count", 0)
        print(f"   {status_icon} {source}: {count} 条")

    # 2. 情感分析
    print("\n【步骤2】分析评论情感...")
    print("-" * 40)

    analyzed_comments = crawler.analyze_sentiment(all_comments)

    # 按情感分组显示
    sentiment_counts = {}
    for comment in analyzed_comments:
        sentiment = comment.get("sentiment", "neutral")
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

    print("\n😊 情感分析结果:")
    for sentiment, count in sentiment_counts.items():
        print(f"   {sentiment}: {count} 条")

    # 3. 保存评论
    print("\n【步骤3】保存评论数据...")
    print("-" * 40)

    comments_file = crawler.save_comments(analyzed_comments, args.keyword)

    print("\n" + "=" * 60)
    print("✅ 工作流完成！")
    print("=" * 60)
    print(f"\n📂 输出目录: {crawler.output_dir}")
    print(f"📄 评论文件: {comments_file}")
    print("\n🎯 下一步:")
    print("   1. 查看保存的评论JSON文件")
    print("   2. 分析用户舆情和真实评价")
    print("   3. 提取有用的细节信息")


def main():
    """同步入口函数"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
