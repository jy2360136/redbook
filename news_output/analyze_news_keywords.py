# -*- coding: utf-8 -*-
"""
新闻关键词分析工具
支持多种方法提取关键词和实体
"""

import json
import re
from collections import Counter
from pathlib import Path

# ============================================
# 方法一：预设关键词统计
# ============================================

def analyze_with_preset_keywords(data, keywords):
    """
    使用预设的关键词列表统计出现次数

    Args:
        data: 新闻JSON数据
        keywords: 预设关键词字典 {关键词: 0}

    Returns:
        排序后的关键词统计结果
    """
    titles = [news['title'] for news in data['news']]

    # 复制一份，避免修改原字典
    result = keywords.copy()

    for title in titles:
        for keyword in result:
            if keyword in title:
                result[keyword] += 1

    # 过滤并排序
    sorted_result = sorted(
        [(k, v) for k, v in result.items() if v > 0],
        key=lambda x: x[1],
        reverse=True
    )

    return sorted_result


# ============================================
# 方法二：简单分词 + 词频统计（无需外部库）
# ============================================

def analyze_with_simple_segmentation(data, min_length=2, min_freq=3):
    """
    使用简单规则分词，统计词频

    优点：不需要安装任何库
    缺点：分词不够精确，可能把长词拆开

    Args:
        data: 新闻JSON数据
        min_length: 最小词长度
        min_freq: 最小出现次数

    Returns:
        词频统计结果
    """
    titles = [news['title'] for news in data['news']]
    all_text = ' '.join(titles)

    # 停用词表（常见无意义词）
    stopwords = {
        '的', '了', '是', '在', '和', '与', '或', '等', '都', '也',
        '这', '那', '有', '被', '把', '让', '给', '到', '从', '为',
        '一个', '什么', '怎么', '如何', '为什么', '哪些', '可以',
        '可能', '应该', '需要', '已经', '正在', '还将', '他们',
        '我们', '你们', '自己', '这个', '那个', '这些', '那些',
        '一篇', '一次', '一起', '一直', '一些', '一种', '一样',
        '之后', '之前', '之后', '之中', '之间', '里面', '这里',
        '还是', '只是', '但是', '因为', '所以', '如果', '虽然',
        '不是', '没有', '不会', '不能', '不要', '只是', '还有',
        '就是', '也是', '都是', '就在', '要说', '来看', '来看',
        '作者', '来源', '时间', '小时', '分钟', '年前', '年后',
        '记者', '编辑', '报道', '文章', '内容', '标题', '图片',
        '真的', '其实', '似乎', '好像', '已经', '还是', '只是',
    }

    # 使用正则提取中文词组（连续2-10个汉字）
    words = re.findall(r'[\u4e00-\u9fa5]{2,10}', all_text)

    # 过滤停用词
    filtered_words = [w for w in words if w not in stopwords and len(w) >= min_length]

    # 统计词频
    word_freq = Counter(filtered_words)

    # 过滤低频词
    result = [(word, count) for word, count in word_freq.items() if count >= min_freq]

    # 排序
    result.sort(key=lambda x: x[1], reverse=True)

    return result


# ============================================
# 方法三：使用jieba分词（需要安装jieba）
# ============================================

def analyze_with_jieba(data, min_freq=3, top_k=100):
    """
    使用jieba分词进行更精确的词频统计和关键词提取

    需要先安装: pip install jieba

    Args:
        data: 新闻JSON数据
        min_freq: 最小出现次数
        top_k: 返回前K个关键词

    Returns:
        词频统计结果和TF-IDF关键词
    """
    try:
        import jieba
        import jieba.analyse
    except ImportError:
        print("❌ 需要先安装jieba: pip install jieba")
        return None, None

    titles = [news['title'] for news in data['news']]
    all_text = ' '.join(titles)

    # 停用词表
    stopwords = {
        '的', '了', '是', '在', '和', '与', '或', '等', '都', '也',
        '这', '那', '有', '被', '把', '让', '给', '到', '从', '为',
        '一个', '什么', '怎么', '如何', '为什么', '哪些', '可以',
        '可能', '应该', '需要', '已经', '正在', '还将', '他们',
        '我们', '你们', '自己', '这个', '那个', '这些', '那些',
        '一篇', '一次', '一起', '一直', '一些', '一种', '一样',
        '作者', '来源', '时间', '小时', '分钟', '年前', '年后',
        '记者', '编辑', '报道', '文章', '内容', '标题', '图片',
    }

    # ========== 词频统计 ==========
    words = jieba.cut(all_text)
    filtered_words = [w for w in words if w not in stopwords and len(w) >= 2 and not w.isdigit()]
    word_freq = Counter(filtered_words)

    freq_result = [(word, count) for word, count in word_freq.items() if count >= min_freq]
    freq_result.sort(key=lambda x: x[1], reverse=True)

    # ========== TF-IDF关键词提取 ==========
    tfidf_keywords = jieba.analyse.extract_tags(all_text, topK=top_k, withWeight=True)

    # ========== TextRank关键词提取 ==========
    textrank_keywords = jieba.analyse.textrank(all_text, topK=top_k, withWeight=True)

    return freq_result[:top_k], tfidf_keywords, textrank_keywords


# ============================================
# 方法四：使用Claude/大模型识别实体（模拟）
# ============================================

def extract_entities_with_llm(titles, batch_size=50):
    """
    使用大模型识别命名实体

    这里我们模拟一个简单的实体识别逻辑：
    - 公司名：通常包含"公司"、"集团"、"科技"等
    - 人物名：通常是2-4个字的中文人名
    - 地名：中国城市、国家名
    - 产品名：知名产品

    实际使用时，可以调用Claude API进行更精确的识别

    Args:
        titles: 标题列表
        batch_size: 每批处理的数量

    Returns:
        分类后的实体统计
    """
    # 预设的实体词典（可以扩展）
    companies = {
        '苹果', '华为', '小米', '特斯拉', '比亚迪', '蔚来', '理想', '小鹏',
        'OpenAI', 'Anthropic', '阿里', '腾讯', '字节', '美团', '百度',
        '京东', '拼多多', '网易', '滴滴', '快手', 'B站', '微博',
        '茅台', '五粮液', '宁德时代', '中芯国际', '大疆',
    }

    people = {
        '张雪', '董宇辉', '特朗普', '马斯克', '雷军', '罗永浩',
        '周鸿祎', '俞敏洪', '李佳琦', '薇娅', '罗翔', '张一鸣',
        '马云', '马化腾', '刘强东', '王兴', '黄峥',
    }

    locations = {
        '美国', '中国', '伊朗', '巴基斯坦', '以色列', '俄罗斯', '乌克兰',
        '北京', '上海', '深圳', '广州', '杭州', '武汉', '成都', '重庆',
        '日本', '韩国', '印度', '欧洲', '中东',
    }

    products = {
        'iPhone', 'ChatGPT', 'Claude', 'GPT', '萝卜快跑', 'FSD',
        'Model', 'Sora', 'Midjourney', 'Copilot',
    }

    industries = {
        'AI', '新能源', '电动车', '芯片', '半导体', '互联网', '电商',
        '直播', '外卖', '游戏', '电影', '房地产', '医疗', '教育',
    }

    # 统计
    result = {
        '公司': Counter(),
        '人物': Counter(),
        '地点': Counter(),
        '产品': Counter(),
        '行业': Counter(),
    }

    all_text = ' '.join(titles)

    for company in companies:
        if company in all_text:
            result['公司'][company] = all_text.count(company)

    for person in people:
        if person in all_text:
            result['人物'][person] = all_text.count(person)

    for location in locations:
        if location in all_text:
            result['地点'][location] = all_text.count(location)

    for product in products:
        if product in all_text:
            result['产品'][product] = all_text.count(product)

    for industry in industries:
        if industry in all_text:
            result['行业'][industry] = all_text.count(industry)

    # 排序
    for category in result:
        result[category] = result[category].most_common()

    return result


# ============================================
# 主程序
# ============================================

def main():
    # 读取数据
    data_file = Path(__file__).parent / 'news_output' / 'news_output_20260405_090257.json'

    if not data_file.exists():
        print(f"[ERROR] File not found: {data_file}")
        return

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📊 数据概览：共 {data['total']} 篇新闻")
    print(f"📰 来源分布：{data['by_source']}")
    print()

    # ========== 方法一：预设关键词 ==========
    print("=" * 60)
    print("📌 方法一：预设关键词统计")
    print("=" * 60)

    preset_keywords = {
        # AI相关
        'AI': 0, 'OpenAI': 0, 'Anthropic': 0, 'Claude': 0, 'GPT': 0,
        # 科技公司
        '苹果': 0, '华为': 0, '小米': 0, '特斯拉': 0,
        '比亚迪': 0, '蔚来': 0, '理想': 0, '小鹏': 0,
        # 中国大厂
        '阿里': 0, '腾讯': 0, '字节': 0, '美团': 0, '百度': 0, '京东': 0,
        # 行业
        '新能源': 0, '电动车': 0, '汽车': 0, '芯片': 0, '半导体': 0,
        # 热门人物
        '张雪': 0, '董宇辉': 0, '特朗普': 0, '马斯克': 0,
        # 热门事件
        '萝卜快跑': 0, '无人驾驶': 0, '自动驾驶': 0,
        '伊朗': 0, '美国': 0,
        # 消费
        '茅台': 0, '白酒': 0, '外卖': 0, '直播': 0, '带货': 0,
        # 其他
        '房地产': 0, '医药': 0, '游戏': 0, '电影': 0,
    }

    result1 = analyze_with_preset_keywords(data, preset_keywords)
    print("\n关键词出现次数 TOP20:")
    for keyword, count in result1[:20]:
        print(f"  {keyword}: {count}")

    # ========== 方法二：简单分词 ==========
    print()
    print("=" * 60)
    print("📌 方法二：简单分词 + 词频统计")
    print("=" * 60)

    result2 = analyze_with_simple_segmentation(data, min_length=2, min_freq=5)
    print("\n高频词 TOP30（自动提取）:")
    for word, count in result2[:30]:
        print(f"  {word}: {count}")

    # ========== 方法三：jieba分词 ==========
    print()
    print("=" * 60)
    print("📌 方法三：jieba分词（需要安装jieba）")
    print("=" * 60)

    result3_freq, result3_tfidf, result3_textrank = analyze_with_jieba(data)

    if result3_freq:
        print("\n词频统计 TOP20:")
        for word, count in result3_freq[:20]:
            print(f"  {word}: {count}")

        print("\nTF-IDF关键词 TOP20:")
        for word, weight in result3_tfidf[:20]:
            print(f"  {word}: {weight:.2f}")

        print("\nTextRank关键词 TOP20:")
        for word, weight in result3_textrank[:20]:
            print(f"  {word}: {weight:.2f}")

    # ========== 方法四：实体识别 ==========
    print()
    print("=" * 60)
    print("📌 方法四：实体识别（分类统计）")
    print("=" * 60)

    titles = [news['title'] for news in data['news']]
    entities = extract_entities_with_llm(titles)

    for category, items in entities.items():
        if items:
            print(f"\n【{category}】出现次数:")
            for name, count in items[:10]:
                print(f"  {name}: {count}")

    # ========== 生成分析报告 ==========
    print()
    print("=" * 60)
    print("📋 分析总结")
    print("=" * 60)

    # 找出最热门的话题
    top_topics = result1[:10]
    print("\n🔥 最热门话题 TOP10:")
    for i, (topic, count) in enumerate(top_topics, 1):
        print(f"  {i}. {topic} ({count}篇)")

    print("\n💡 建议:")
    print("  - 以上话题出现频率最高，适合作为视频选题")
    print("  - 建议选择时效性强、争议性大的话题深度分析")


if __name__ == '__main__':
    main()