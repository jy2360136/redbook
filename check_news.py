import json
import os

# 查找最新的 JSON 文件
output_dir = "news_output"
json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
if not json_files:
    print("未找到 JSON 文件")
    exit()

latest_file = max(json_files)
filepath = os.path.join(output_dir, latest_file)

# 读取数据
with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 60)
print("📊 新闻爬取统计")
print("=" * 60)
print(f"📁 文件：{latest_file}")
print(f"⏰ 抓取时间：{data['fetch_time']}")
print(f"📈 总新闻数：{data['total']} 条")
print()
print("📋 各来源分布:")
for source, count in data['by_source'].items():
    print(f"  - {source}: {count} 条")

print()
print("📰 最新 10 条新闻:")
print("-" * 60)
for i, news in enumerate(data['news'][:10], 1):
    print(f"{i}. [{news['source']}]")
    print(f"   标题：{news['title']}")
    print(f"   链接：{news['link']}")
    if 'published' in news and news['published']:
        print(f"   时间：{news['published']}")
    print()

print("=" * 60)
print("✅ 数据已成功保存！")
print("=" * 60)
