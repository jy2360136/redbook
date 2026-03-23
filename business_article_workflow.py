"""
商业短文自动化工作流
====================
目标：以热点新闻为引子，深度解读知名公司，生成商业分析短文

工作流：
1. 搜索财经网站 -> 筛选包含知名公司的新闻 -> 生成JSON
2. 按大纲生成文章：
   - 事件描述
   - 事件原因分析
   - 公司现状（困境+优势）
   - 公司历史背景
   - 延伸内容（黑料/爆点）

平台适配：
- 小红书/抖音：短文案 (~1000字，3分钟)
- 微信公众号/B站：长文案 (~3000字，10分钟)
"""

import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import requests
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# 尝试导入可选依赖
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️  BeautifulSoup4 未安装，运行: pip install beautifulsoup4")

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("⚠️  feedparser 未安装，运行: pip install feedparser")


# ==================== 配置 ====================

# 知名公司名单（家喻户晓的公司）
FAMOUS_COMPANIES = {
    # 汽车行业
    "丰田": {"sector": "汽车", "keywords": ["丰田", "TOYOTA"]},
    "本田": {"sector": "汽车", "keywords": ["本田", "HONDA"]},
    "比亚迪": {"sector": "汽车", "keywords": ["比亚迪", "BYD"]},
    "特斯拉": {"sector": "汽车", "keywords": ["特斯拉", "Tesla", "马斯克"]},
    "蔚来": {"sector": "汽车", "keywords": ["蔚来", "NIO"]},
    "理想": {"sector": "汽车", "keywords": ["理想汽车", "李想"]},
    "小鹏": {"sector": "汽车", "keywords": ["小鹏", "XPeng"]},
    "小米": {"sector": "科技", "keywords": ["小米", "Xiaomi", "雷军"]},

    # 科技互联网
    "华为": {"sector": "科技", "keywords": ["华为", "Huawei", "任正非"]},
    "苹果": {"sector": "科技", "keywords": ["苹果", "Apple", "库克"]},
    "腾讯": {"sector": "互联网", "keywords": ["腾讯", "Tencent", "马化腾", "微信"]},
    "阿里": {"sector": "互联网", "keywords": ["阿里", "阿里巴巴", "Alibaba", "马云", "淘宝", "天猫"]},
    "字节": {"sector": "互联网", "keywords": ["字节", "ByteDance", "抖音", "TikTok", "张一鸣"]},
    "百度": {"sector": "互联网", "keywords": ["百度", "Baidu", "李彦宏"]},
    "京东": {"sector": "互联网", "keywords": ["京东", "JD", "刘强东"]},
    "美团": {"sector": "互联网", "keywords": ["美团", "Meituan", "王兴"]},
    "拼多多": {"sector": "互联网", "keywords": ["拼多多", "PDD", "黄峥"]},

    # 金融
    "茅台": {"sector": "消费", "keywords": ["茅台", "Moutai"]},
    "宁德时代": {"sector": "新能源", "keywords": ["宁德时代", "CATL", "曾毓群"]},

    # 手机
    "OPPO": {"sector": "科技", "keywords": ["OPPO", "欧珀"]},
    "vivo": {"sector": "科技", "keywords": ["vivo", "维沃"]},

    # 其他知名
    "海尔": {"sector": "家电", "keywords": ["海尔", "Haier"]},
    "格力": {"sector": "家电", "keywords": ["格力", "Gree", "董明珠"]},
    "联想": {"sector": "科技", "keywords": ["联想", "Lenovo"]},
    "网易": {"sector": "互联网", "keywords": ["网易", "NetEase", "丁磊"]},
    "快手": {"sector": "互联网", "keywords": ["快手", "Kuaishou"]},
    "B站": {"sector": "互联网", "keywords": ["B站", "哔哩哔哩", "bilibili"]},
}


class Platform(Enum):
    """平台类型"""
    XIAOHONGSHU = "xiaohongshu"  # 小红书
    DOUYIN = "douyin"            # 抖音
    WECHAT = "wechat"            # 微信公众号
    BILIBILI = "bilibili"        # B站


@dataclass
class ArticleOutline:
    """文章大纲"""
    # 事件描述
    event_title: str = ""
    event_summary: str = ""
    event_details: str = ""

    # 原因分析
    reasons: List[str] = None
    deep_analysis: str = ""

    # 公司现状
    company_name: str = ""
    current_situation: str = ""
    challenges: List[str] = None
    advantages: List[str] = None

    # 公司历史
    founding_history: str = ""
    founder_info: str = ""
    milestone_events: List[str] = None

    # 延伸内容
    controversies: List[str] = None  # 争议/黑料
    interesting_facts: List[str] = None  # 有趣的事实
    future_outlook: str = ""

    # 投资视角
    investment_view: str = ""
    related_stocks: List[str] = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []
        if self.challenges is None:
            self.challenges = []
        if self.advantages is None:
            self.advantages = []
        if self.milestone_events is None:
            self.milestone_events = []
        if self.controversies is None:
            self.controversies = []
        if self.interesting_facts is None:
            self.interesting_facts = []
        if self.related_stocks is None:
            self.related_stocks = []


# ==================== 新闻抓取器 ====================

class NewsFetcher:
    """新闻抓取器"""

    def __init__(self, output_dir: str = "./news_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def fetch_huxiu(self) -> List[Dict]:
        """抓取虎嗅网"""
        if not HAS_FEEDPARSER:
            return []

        print("📰 正在抓取虎嗅网...")
        news_list = []

        try:
            feed = feedparser.parse("https://www.huxiu.com/rss/0.xml")
            for entry in feed.entries[:15]:
                news = {
                    "source": "虎嗅网",
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": self._clean_html(entry.get("summary", "")),
                    "published": entry.get("published", ""),
                }
                news_list.append(news)
            print(f"✅ 虎嗅网: {len(news_list)} 条")
        except Exception as e:
            print(f"❌ 虎嗅网失败: {e}")

        return news_list

    def fetch_36kr(self) -> List[Dict]:
        """抓取36氪"""
        print("📰 正在抓取36氪...")
        news_list = []

        try:
            api_url = "https://gateway.36kr.com/api/miscre/home/topic/newsflashes"
            headers = {**self.headers, "Content-Type": "application/json"}
            data = {"pageSize": 20, "pageEvent": 1, "platformId": 2}

            response = requests.post(api_url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                items = result.get("data", {}).get("itemList", [])
                for item in items[:15]:
                    news = {
                        "source": "36氪",
                        "title": item.get("title", ""),
                        "link": f"https://36kr.com/newsflashes/{item.get('id', '')}",
                        "summary": item.get("description", ""),
                        "published": str(item.get("publishTime", "")),
                    }
                    news_list.append(news)
                print(f"✅ 36氪: {len(news_list)} 条")
        except Exception as e:
            print(f"❌ 36氪失败: {e}")

        return news_list

    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    def fetch_all(self) -> List[Dict]:
        """抓取所有新闻源"""
        all_news = []
        all_news.extend(self.fetch_huxiu())
        all_news.extend(self.fetch_36kr())
        return all_news


# ==================== 公司识别与筛选 ====================

class CompanyDetector:
    """公司识别器 - 从新闻标题中识别知名公司"""

    def __init__(self, companies: Dict = FAMOUS_COMPANIES):
        self.companies = companies
        self._build_keyword_map()

    def _build_keyword_map(self):
        """构建关键词到公司的映射"""
        self.keyword_to_company = {}
        for company_name, info in self.companies.items():
            for kw in info["keywords"]:
                self.keyword_to_company[kw.lower()] = company_name

    def detect_company(self, title: str) -> Optional[Tuple[str, str]]:
        """
        从标题中检测公司
        返回: (公司名, 行业) 或 None
        """
        title_lower = title.lower()
        for keyword, company_name in self.keyword_to_company.items():
            if keyword in title_lower:
                sector = self.companies[company_name]["sector"]
                return (company_name, sector)
        return None

    def filter_news_by_company(self, news_list: List[Dict]) -> List[Dict]:
        """筛选包含知名公司的新闻"""
        filtered = []
        for news in news_list:
            result = self.detect_company(news["title"])
            if result:
                news["company"] = result[0]
                news["sector"] = result[1]
                filtered.append(news)

        # 按公司分组统计
        company_counts = {}
        for news in filtered:
            company = news["company"]
            company_counts[company] = company_counts.get(company, 0) + 1

        # 按出现次数排序
        filtered.sort(key=lambda x: company_counts.get(x["company"], 0), reverse=True)

        return filtered


# ==================== 文章生成器 ====================

class ArticleGenerator:
    """商业短文生成器"""

    # 不同平台的字数限制
    WORD_LIMITS = {
        Platform.XIAOHONGSHU: 1000,
        Platform.DOUYIN: 1000,
        Platform.WECHAT: 3000,
        Platform.BILIBILI: 3000,
    }

    def __init__(self, output_dir: str = "./news_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.detector = CompanyDetector()

    def create_article_prompt(
        self,
        news: Dict,
        platform: Platform = Platform.XIAOHONGSHU,
        company_info: Dict = None
    ) -> str:
        """
        生成文章写作的 Prompt
        这个 Prompt 可以发给 Claude/GPT 进行深度创作
        """
        company = news.get("company", "该公司")
        sector = news.get("sector", "")
        word_limit = self.WORD_LIMITS.get(platform, 1000)

        prompt = f"""
# 任务：撰写商业分析短文

请根据以下热点新闻，撰写一篇关于 **{company}** 的深度商业分析文章。

## 热点新闻
- **标题**: {news['title']}
- **来源**: {news['source']}
- **摘要**: {news['summary'][:500]}
- **链接**: {news['link']}

## 写作要求

### 平台: {platform.value}
### 字数限制: {word_limit}字左右

### 文章结构（请严格按照以下大纲）

#### 第一部分：事件引爆点（150-200字）
- 用爆炸性的语言描述这个新闻事件
- 突出数字、对比、反差
- 吸引读者继续阅读

#### 第二部分：事件背后的原因（200-300字）
- 分析事件发生的深层原因
- 可以搜索延伸相关背景
- 列出2-3个关键原因

#### 第三部分：公司现状分析（200-300字）
- **当前困境**：列出2-3个面临的挑战
- **核心优势**：列出2-3个仍然强大的地方
- 客观分析，不吹不黑

#### 第四部分：公司历史背景（150-200字）
- 何时创建？由谁创建？
- 创始人背景故事
- 关键发展里程碑（2-3个）

#### 第五部分：延伸爆点内容（100-200字）
- 历史上的争议事件/黑料
- 有趣的冷知识
- 行业内幕
- （可以搜索挖掘）

#### 第六部分：投资视角（100字，可选）
- 对A股相关板块的影响
- 投资者应该关注什么

### 写作风格
- 口语化、易读、有节奏感
- 适当使用短句和感叹号
- 数据要准确，观点要鲜明
- 结尾留有讨论空间

### 禁止
- 不要使用"综上所述"、"总而言之"等老套结尾
- 不要堆砌专业术语
- 不要写成公关稿

---

请以 Markdown 格式输出文章。
"""
        return prompt

    def create_research_prompts(self, company: str) -> List[str]:
        """
        生成用于搜索延伸内容的 Prompt
        可以用 WebSearch 工具执行
        """
        prompts = [
            f"搜索 {company} 公司的创始人和创立历史",
            f"搜索 {company} 公司的重大争议事件和负面新闻",
            f"搜索 {company} 公司近两年的财务状况和业绩",
            f"搜索 {company} 公司面临的挑战和竞争对手",
            f"搜索 {company} 公司的有趣冷知识和行业内幕",
        ]
        return prompts

    def save_article(
        self,
        article_content: str,
        news: Dict,
        platform: Platform,
        outline: ArticleOutline = None
    ) -> str:
        """保存文章"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        company = news.get("company", "unknown")
        filename = f"article_{company}_{platform.value}_{timestamp}.md"
        filepath = self.output_dir / filename

        # 构建完整的文章文件
        header = f"""---
title: {news['title']}
company: {company}
platform: {platform.value}
created: {datetime.now().isoformat()}
source: {news['source']}
source_url: {news['link']}
---

"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header + article_content)

        print(f"💾 文章已保存: {filepath}")
        return str(filepath)

    def save_outline(self, outline: ArticleOutline, company: str) -> str:
        """保存文章大纲"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"outline_{company}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(outline), f, ensure_ascii=False, indent=2)

        return str(filepath)


# ==================== 主工作流 ====================

class BusinessArticleWorkflow:
    """商业短文完整工作流"""

    def __init__(self, output_dir: str = "./news_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.fetcher = NewsFetcher(output_dir)
        self.detector = CompanyDetector()
        self.generator = ArticleGenerator(output_dir)

    def step1_fetch_and_filter(self) -> List[Dict]:
        """步骤1：抓取并筛选新闻"""
        print("\n" + "=" * 60)
        print("【步骤1】抓取新闻并筛选知名公司")
        print("=" * 60)

        # 抓取
        all_news = self.fetcher.fetch_all()
        print(f"\n📊 共抓取 {len(all_news)} 条新闻")

        # 筛选
        filtered = self.detector.filter_news_by_company(all_news)
        print(f"🎯 筛选出 {len(filtered)} 条包含知名公司的新闻")

        # 按公司分组显示
        companies = {}
        for news in filtered:
            company = news["company"]
            if company not in companies:
                companies[company] = []
            companies[company].append(news)

        print("\n📈 公司新闻分布:")
        for company, news_list in sorted(companies.items(), key=lambda x: -len(x[1])):
            print(f"   {company}: {len(news_list)} 条")

        # 保存
        news_file = self.output_dir / f"filtered_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(news_file, 'w', encoding='utf-8') as f:
            json.dump({
                "fetch_time": datetime.now().isoformat(),
                "total": len(filtered),
                "by_company": {k: len(v) for k, v in companies.items()},
                "news": filtered
            }, f, ensure_ascii=False, indent=2)
        print(f"\n💾 新闻已保存: {news_file}")

        return filtered

    def step2_select_target(self, filtered_news: List[Dict]) -> Dict:
        """步骤2：选择目标新闻"""
        print("\n" + "=" * 60)
        print("【步骤2】选择目标新闻")
        print("=" * 60)

        # 按公司分组
        companies = {}
        for news in filtered_news:
            company = news["company"]
            if company not in companies:
                companies[company] = []
            companies[company].append(news)

        # 选择新闻最多的公司
        if not companies:
            print("❌ 没有找到包含知名公司的新闻")
            return None

        top_company = max(companies.keys(), key=lambda k: len(companies[k]))
        top_news_list = companies[top_company]

        print(f"\n🔥 热度最高的公司: {top_company} ({len(top_news_list)} 条相关新闻)")
        print("\n相关新闻:")
        for i, news in enumerate(top_news_list[:5], 1):
            print(f"  {i}. {news['title'][:50]}...")

        # 选择第一条
        target_news = top_news_list[0]
        print(f"\n✅ 已选择: {target_news['title']}")

        return target_news

    def step3_generate_prompts(self, news: Dict, platform: Platform = Platform.XIAOHONGSHU) -> str:
        """步骤3：生成写作 Prompt"""
        print("\n" + "=" * 60)
        print("【步骤3】生成写作提示词")
        print("=" * 60)

        company = news.get("company", "该公司")
        print(f"\n📝 目标公司: {company}")
        print(f"📱 发布平台: {platform.value}")

        # 生成主文章 Prompt
        main_prompt = self.generator.create_article_prompt(news, platform)

        # 保存 Prompt
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prompt_file = self.output_dir / f"prompt_{company}_{timestamp}.md"

        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(main_prompt)

        print(f"\n💾 写作提示词已保存: {prompt_file}")

        # 生成延伸搜索 Prompt
        research_prompts = self.generator.create_research_prompts(company)
        research_file = self.output_dir / f"research_prompts_{company}_{timestamp}.txt"

        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(f"# {company} 延伸内容搜索提示词\n\n")
            for i, p in enumerate(research_prompts, 1):
                f.write(f"{i}. {p}\n")

        print(f"💾 搜索提示词已保存: {research_file}")

        # 显示 Prompt 预览
        print("\n" + "-" * 40)
        print("📋 写作提示词预览:")
        print("-" * 40)
        print(main_prompt[:800] + "...")

        return str(prompt_file)

    def run(self, platform: Platform = Platform.XIAOHONGSHU) -> Dict:
        """运行完整工作流"""
        print("\n" + "🚀" * 30)
        print("商业短文自动化工作流")
        print("🚀" * 30)

        # 步骤1：抓取筛选
        filtered_news = self.step1_fetch_and_filter()
        if not filtered_news:
            return {"success": False, "error": "没有找到合适的新闻"}

        # 步骤2：选择目标
        target_news = self.step2_select_target(filtered_news)
        if not target_news:
            return {"success": False, "error": "没有找到目标新闻"}

        # 步骤3：生成 Prompt
        prompt_file = self.step3_generate_prompts(target_news, platform)

        return {
            "success": True,
            "target_news": target_news,
            "prompt_file": prompt_file,
            "next_step": "将 prompt_file 的内容发给 Claude/GPT 进行文章创作"
        }


# ==================== 入口 ====================

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="商业短文工作流")
    parser.add_argument(
        "--platform",
        choices=["xiaohongshu", "douyin", "wechat", "bilibili"],
        default="xiaohongshu",
        help="目标平台"
    )

    args = parser.parse_args()
    platform = Platform(args.platform)

    workflow = BusinessArticleWorkflow()
    result = workflow.run(platform)

    if result["success"]:
        print("\n" + "=" * 60)
        print("✅ 工作流完成！")
        print("=" * 60)
        print(f"\n📂 下一步:")
        print(f"   1. 打开 {result['prompt_file']}")
        print(f"   2. 复制内容发给 Claude/GPT")
        print(f"   3. 获得生成的文章")
        print(f"   4. 用 Banana/Midjourney 生成配图")
        print(f"   5. 发布到 {platform.value}")
    else:
        print(f"\n❌ 工作流失败: {result.get('error')}")


if __name__ == "__main__":
    main()
