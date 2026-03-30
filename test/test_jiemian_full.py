#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试界面新闻爬虫"""

from financial_news_workflow_crawl4ai import SourceJiemian

print("=" * 50)
print("测试界面新闻爬虫（10 天）")
print("=" * 50)

news_list = SourceJiemian.fetch(days=10, filter_companies=False)

print(f"\n✅ 成功抓取 {len(news_list)} 条新闻")
print("\n前 10 条:")
for i, news in enumerate(news_list[:10], 1):
    print(f"{i}. {news['title'][:50]}... | {news['published']}")
