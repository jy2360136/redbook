"""
测试主程序整合情况
验证标题格式和文件输出规范
"""

import json
from pathlib import Path

def test_integration():
    """测试主程序整合"""
    
    # 查找最新的输出文件
    output_dir = Path("news_output")
    json_files = sorted(output_dir.glob("news_output_*.json"))
    
    if not json_files:
        print("❌ 未找到任何输出文件")
        return
    
    latest_file = json_files[-1]
    print(f"📄 检查文件：{latest_file.name}")
    
    # 读取 JSON
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    news_list = data.get("news", [])
    total = data.get("total", 0)
    by_source = data.get("by_source", {})
    
    print(f"\n📊 总体统计:")
    print(f"  总数：{total} 条")
    print(f"  来源：{by_source}")
    
    # 检查钛媒体新闻
    tmtpost_news = [n for n in news_list if n.get("source") == "钛媒体"]
    
    if tmtpost_news:
        print(f"\n🔍 钛媒体新闻检查:")
        print(f"  数量：{len(tmtpost_news)} 条")
        
        # 检查标题格式
        has_summary = 0
        no_summary = 0
        
        for news in tmtpost_news[:10]:  # 检查前 10 条
            title = news.get("title", "")
            if "——" in title:
                has_summary += 1
            else:
                no_summary += 1
        
        print(f"\n  标题格式（前 10 条）:")
        print(f"    ✅ 包含 summary: {has_summary} 条")
        print(f"    ⚠️  无 summary: {no_summary} 条")
        
        # 显示示例
        print(f"\n  示例（前 3 条）:")
        for i, news in enumerate(tmtpost_news[:3], 1):
            title = news.get("title", "")
            link = news.get("link", "")
            published = news.get("published", "")
            
            print(f"\n  {i}. 标题：{title[:80]}...")
            print(f"     链接：{link}")
            print(f"     时间：{published}")
        
        # 检查字段完整性
        print(f"\n  字段完整性检查:")
        required_fields = ["source", "title", "link", "published"]
        all_have_fields = True
        
        for news in tmtpost_news:
            for field in required_fields:
                if field not in news:
                    print(f"    ❌ 缺少字段：{field}")
                    all_have_fields = False
        
        if all_have_fields:
            print(f"    ✅ 所有新闻都包含必需字段")
        
        # 视频过滤检查
        video_count = sum(1 for n in tmtpost_news if "/video/" in n.get("link", "").lower())
        print(f"\n  视频过滤:")
        print(f"    ✅ 文字新闻：{len(tmtpost_news) - video_count} 条")
        print(f"    ❌ 视频新闻：{video_count} 条")
        
        if video_count == 0:
            print(f"    🎉 视频过滤成功！")
        else:
            print(f"    ⚠️  发现 {video_count} 条视频新闻混入！")
    
    # 检查文件名规范
    print(f"\n📁 文件名规范检查:")
    expected_pattern = "news_output_YYYYMMDD_HHMMSS.json"
    actual_name = latest_file.name
    
    import re
    pattern = r"news_output_\d{8}_\d{6}\.json"
    if re.match(pattern, actual_name):
        print(f"  ✅ 符合规范：{actual_name}")
        print(f"     格式：{expected_pattern}")
    else:
        print(f"  ❌ 不符合规范：{actual_name}")
        print(f"     应为：{expected_pattern}")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")


if __name__ == "__main__":
    test_integration()
