"""
钛媒体爬虫测试脚本
验证视频过滤功能是否正常工作
"""

import json
from pathlib import Path

def test_video_filter():
    """测试视频新闻是否被过滤"""
    
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
    
    print(f"📊 总数：{total} 条")
    print(f"📊 来源统计：{data.get('by_source', {})}")
    
    # 检查是否有视频新闻混入
    video_count = 0
    text_count = 0
    
    for news in news_list:
        link = news.get("link", "")
        title = news.get("title", "")
        
        # 检查链接是否包含 /video/
        if "/video/" in link.lower():
            video_count += 1
            print(f"❌ 发现视频新闻：{title}")
            print(f"   链接：{link}")
        else:
            text_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ 文字新闻：{text_count} 条")
    print(f"❌ 视频新闻：{video_count} 条")
    
    if video_count == 0:
        print("\n🎉 视频过滤成功！所有新闻都是文字类型。")
    else:
        print(f"\n⚠️  发现 {video_count} 条视频新闻混入，需要修复！")
    
    # 显示前 10 条新闻的链接类型
    print("\n前 10 条新闻链接类型:")
    for i, news in enumerate(news_list[:10], 1):
        link = news.get("link", "")
        title = news.get("title", "")[:30]
        link_type = "🎬 视频" if "/video/" in link else "📝 文字"
        print(f"  {i}. {link_type} - {title}...")
        print(f"     链接：{link}")


if __name__ == "__main__":
    test_video_filter()
