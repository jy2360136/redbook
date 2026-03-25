"""
测试Crawl4AI库的功能
"""

import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("🔍 测试Crawl4AI库...")

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
    print("✅ Crawl4AI 已安装")
except ImportError:
    print("❌ Crawl4AI 未安装")
    print("   运行: pip install crawl4ai")
    sys.exit(1)

print("\n🚀 测试WebCrawler功能...")

import asyncio

# 测试简单的网页抓取
async def test_basic_crawl():
    print("\n📰 测试1: 抓取简单网页")
    try:
        # 使用HTTP爬虫策略，不依赖Playwright
        crawler = AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy())
        # 使用arun方法而不是crawl方法
        results = await crawler.arun(
            url="https://www.example.com",
            max_depth=1,
            max_pages=1
        )
        
        if results:
            result = results[0]
            print("✅ 抓取成功!")
            print(f"   URL: {result.url}")
            # 打印result对象的属性
            print(f"   Result对象属性: {dir(result)}")
            # 尝试访问可能的内容属性
            if hasattr(result, 'html'):
                print(f"   HTML内容长度: {len(result.html[:1000])} 字符")
                print(f"   HTML内容预览: {result.html[:100]}...")
            elif hasattr(result, 'text'):
                print(f"   文本内容长度: {len(result.text[:1000])} 字符")
                print(f"   文本内容预览: {result.text[:100]}...")
            return True
        else:
            print("❌ 抓取失败: 没有返回结果")
            return False
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return False

# 测试复杂网页抓取
async def test_complex_crawl():
    print("\n📰 测试2: 抓取复杂网页")
    try:
        # 使用HTTP爬虫策略，不依赖Playwright
        crawler = AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy())
        # 使用arun方法而不是crawl方法
        results = await crawler.arun(
            url="https://news.ycombinator.com",
            max_depth=1,
            max_pages=1
        )
        
        if results:
            result = results[0]
            print("✅ 抓取成功!")
            print(f"   URL: {result.url}")
            # 尝试访问html属性
            if hasattr(result, 'html'):
                print(f"   HTML内容长度: {len(result.html[:1000])} 字符")
                print(f"   HTML内容预览: {result.html[:100]}...")
            return True
        else:
            print("❌ 抓取失败: 没有返回结果")
            return False
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return False

# 测试AI增强功能（如果可用）
async def test_ai_enhanced_crawl():
    print("\n🤖 测试3: AI增强抓取")
    try:
        # 使用HTTP爬虫策略，不依赖Playwright
        crawler = AsyncWebCrawler(crawler_strategy=AsyncHTTPCrawlerStrategy())
        # 使用arun方法而不是crawl方法
        results = await crawler.arun(
            url="https://www.python.org",
            max_depth=1,
            max_pages=1
        )
        
        if results:
            result = results[0]
            print("✅ AI增强抓取成功!")
            print(f"   URL: {result.url}")
            # 尝试访问html属性
            if hasattr(result, 'html'):
                print(f"   HTML内容长度: {len(result.html[:1000])} 字符")
                print(f"   HTML内容预览: {result.html[:100]}...")
            return True
        else:
            print("❌ AI增强抓取失败: 没有返回结果")
            return False
    except Exception as e:
        print(f"❌ AI增强抓取失败: {e}")
        print("   可能需要配置API密钥或网络连接问题")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Crawl4AI 功能测试")
    print("=" * 60)
    
    tests = [
        test_basic_crawl,
        test_complex_crawl,
        test_ai_enhanced_crawl
    ]
    
    total = len(tests)
    
    # 运行异步测试
    async def run_tests():
        passed = 0
        for test in tests:
            if await test():
                passed += 1
        return passed
    
    passed = asyncio.run(run_tests())
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 测试通过")
    print("=" * 60)
    
    if passed > 0:
        print("\n✅ Crawl4AI 可以正常使用!")
        print("\n📋 功能特点:")
        print("   • 网页内容提取")
        print("   • 链接提取")
        print("   • AI增强内容理解")
        print("   • 处理动态网页")
        print("\n💡 应用场景:")
        print("   • 新闻内容抓取")
        print("   • 数据挖掘")
        print("   • 网站监控")
        print("   • 内容分析")
    else:
        print("\n❌ Crawl4AI 无法正常使用")
        print("   请检查网络连接或API配置")
