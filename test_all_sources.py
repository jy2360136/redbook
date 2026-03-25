import sys
import io
import json
import traceback

from financial_news_workflow_crawl4ai import (
    SourceHuxiu, Source36kr, SourceTmtpost, SourceJiemian,
    SourceGeekpark, SourceLatepost, SourceThepaper
)
import financial_news_workflow_crawl4ai
financial_news_workflow_crawl4ai.FAMOUS_COMPANIES = [""]

sources = [
    SourceHuxiu, Source36kr, SourceTmtpost, SourceJiemian,
    SourceGeekpark, SourceLatepost, SourceThepaper
]

def test_sources():
    print("开始测试7大媒体源...")
    results = {}
    
    for source_class in sources:
        name = source_class.name
        print(f"\n[{name}] 测试中...")
        try:
            # 临时移除对公司名的过滤，以测试连通性和基本解析
            # 为此我们稍微修改一下，因为 fetch 方法内部硬编码了过滤。
            # 这里我们还是直接调 fetch()，看能不能抓出数据（如果新闻里正好有公司名）
            # 或者看是否有异常抛出。
            news = source_class.fetch(days=3)
            if news:
                print(f"✅ 成功! 抓取到 {len(news)} 条包含目标公司名的新闻。")
                print(f"   示例: {news[0]['title']} -> {news[0]['link']}")
                results[name] = {"status": "success", "count": len(news)}
            else:
                print(f"⚠️ 成功执行，但未抓取到包含目标公司名的新闻，或者抓取为0。")
                results[name] = {"status": "empty", "count": 0}
        except Exception as e:
            print(f"❌ 失败! 错误信息: {e}")
            traceback.print_exc()
            results[name] = {"status": "error", "error": str(e)}
            
    print("\n--- 总结 ---")
    for name, res in results.items():
        print(f"{name}: {res['status']} ({res.get('count', res.get('error', ''))})")

if __name__ == '__main__':
    test_sources()
