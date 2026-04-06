# -*- coding: utf-8 -*-
"""
新闻关键词分析工具 v2.0
- 方法二：自动提取高频词
- 方法三：实体识别分类
- 新增：高频大话题细分功能
"""

import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import re
from collections import Counter
from pathlib import Path


class NewsKeywordAnalyzer:
    """新闻关键词分析器"""

    # 停用词表
    STOPWORDS = {
        '的', '了', '是', '在', '和', '与', '或', '等', '都', '也',
        '这', '那', '有', '被', '把', '让', '给', '到', '从', '为',
        '一个', '什么', '怎么', '如何', '为什么', '哪些', '可以',
        '他们', '我们', '你们', '自己', '这个', '那个', '这些', '那些',
        '可能', '应该', '需要', '已经', '正在', '还将', '还是', '只是',
        '但是', '因为', '所以', '如果', '虽然', '不是', '没有', '不会',
        '不能', '不要', '还有', '就是', '也是', '都是', '就在',
        '小时', '年前', '年后', '分钟', '昨天', '今天', '明天',
        # 数量词
        '亿元', '万美元', '万亿', '万人', '个亿', '美元',
        # 媒体词
        '作者', '来源', '记者', '编辑', '报道', '文章', '内容', '标题',
        # 无意义词
        '之后', '正在被', '外媒', '观察', '未来', '全球', '公司',
        '正在', '还能', '还能', '最终', '还是', '已经', '一次', '一个',
        '这场', '这个', '那个', '哪些', '这种', '那种', '这些', '那些',
        '更是', '为何', '如何', '什么', '怎么', '怎样', '多少', '几个',
        '来了', '去了', '说到', '看到', '听到', '想到', '提到',
        '来了', '出了', '进了', '起了', '过了', '过了',
        # 新增停用词
        '为什么', '怎么办', '怎么样', '是什么', '有哪些', '多少人',
        '很多人', '有些人', '所有人', '大多数人', '年轻人', '老年人',
        '中国人', '美国人', '日本人', '韩国人', '欧洲人',
        '一年', '两年', '三年', '五年', '十年', '二十年',
        '第一次', '第二次', '第三次', '最后一次', '第一次',
    }

    # 实体词典
    ENTITY_DICT = {
        '公司': {
            # 科技巨头
            '苹果', '华为', '小米', 'OPPO', 'vivo', '三星',
            '特斯拉', '比亚迪', '蔚来', '理想', '小鹏', '吉利', '零跑',
            # 互联网大厂
            '阿里', '阿里巴巴', '腾讯', '字节', '字节跳动', '美团', '百度',
            '京东', '拼多多', '网易', '滴滴', '快手', 'B站', '微博', '小红书',
            # AI公司
            'OpenAI', 'Anthropic', 'Claude', 'Google', '微软', 'Meta',
            '智谱AI', '月之暗面', 'MiniMax', '百川智能', 'DeepSeek', '深度求索',
            # 传统行业
            '茅台', '五粮液', '宁德时代', '中芯国际', '大疆',
            '恒大', '碧桂园', '万科', '泡泡玛特', '蜜雪冰城', '瑞幸', '海底捞', '呷哺',
            '优必选', '科大讯飞', '商汤', '旷视',
        },
        '人物': {
            '董宇辉', '特朗普', '马斯克', '雷军', '罗永浩',
            '周鸿祎', '俞敏洪', '李佳琦', '薇娅', '罗翔', '张一鸣',
            '马云', '马化腾', '刘强东', '王兴', '黄峥', '李想', '李斌',
            '巴菲特', '孙正义', '黄仁勋', '张雪', '全红婵',
        },
        '地点': {
            '美国', '中国', '伊朗', '巴基斯坦', '以色列', '俄罗斯', '乌克兰',
            '日本', '韩国', '印度', '德国', '英国', '法国',
            '北京', '上海', '深圳', '广州', '杭州', '武汉', '成都', '重庆',
            '南京', '苏州', '西安', '长沙', '郑州', '川渝',
            '欧洲', '中东', '东南亚', '北美', '非洲',
        },
        '行业': {
            'AI', '人工智能', '新能源', '电动车', '芯片', '半导体',
            '互联网', '电商', '直播', '外卖', '游戏', '电影',
            '房地产', '医疗', '教育', '金融', '元宇宙',
            '无人驾驶', '自动驾驶', '萝卜快跑', 'ChatGPT', '大模型',
            'AIGC', 'SaaS', '机器人', '人形机器人',
        },
    }

    # 大话题细分词典 - 当某个话题频次过高时，自动细分
    TOPIC_SUBDIVISIONS = {
        'AI': {
            '关键词': ['Claude', 'OpenAI', 'GPT', '大模型', 'Agent', 'AI应用', 'AI编程',
                      'AI就业', 'AI替代', 'AI安全', 'AIGC', 'AI教育', 'AI医疗',
                      '智谱', 'DeepSeek', '月之暗面', 'Kimi', 'Sora', 'AI搜索',
                      'AI视频', 'AI绘画', 'AI写作', 'AI客服', 'AI助理', '龙虾'],
            '细分维度': ['产品/公司', '应用场景', '社会影响', '安全伦理']
        },
        '苹果': {
            '关键词': ['iPhone', 'iPad', 'Mac', 'Apple Intelligence', '苹果AI',
                      'App Store', '反垄断', 'Vision Pro', '苹果汽车', 'Siri'],
            '细分维度': ['产品线', '政策影响', 'AI战略', '市场竞争']
        },
        '腾讯': {
            '关键词': ['微信', '游戏', '王者荣耀', '腾讯云', '腾讯视频', '腾讯音乐',
                      '腾讯AI', '小程序', '视频号'],
            '细分维度': ['业务线', '产品', '战略']
        },
        '阿里': {
            '关键词': ['淘宝', '天猫', '阿里云', '支付宝', '钉钉', '饿了么', '高德',
                      '阿里巴巴', '淘天', '阿里国际'],
            '细分维度': ['业务线', '产品', '战略']
        },
        '新能源': {
            '关键词': ['比亚迪', '特斯拉', '蔚来', '理想', '小鹏', '零跑', '小米汽车',
                      '动力电池', '充电桩', '新能源车', '电动车', '混动'],
            '细分维度': ['车企', '技术路线', '基础设施', '市场格局']
        },
        '机器人': {
            '关键词': ['人形机器人', '优必选', '宇树', '机器狗', '工业机器人',
                      '服务机器人', '医疗机器人', '机器人第一股'],
            '细分维度': ['类型', '公司', '应用场景']
        }
    }

    def __init__(self, data_file):
        """初始化分析器"""
        self.data_file = Path(data_file)
        self.data = None
        self.titles = None
        self.news_list = None

    def load_data(self):
        """加载数据"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.titles = [news['title'] for news in self.data['news']]
        self.news_list = self.data['news']
        return self

    def extract_high_freq_words(self, min_length=2, min_freq=3, top_n=100):
        """
        方法二：自动提取高频词
        Returns: [(词, 频次), ...]
        """
        all_text = ' '.join(self.titles)
        words = re.findall(r'[\u4e00-\u9fa5]{2,8}', all_text)
        filtered_words = [w for w in words
                          if w not in self.STOPWORDS
                          and len(w) >= min_length]
        word_freq = Counter(filtered_words)
        return word_freq.most_common(top_n)

    def extract_entities(self, top_n=15):
        """
        方法三：实体识别分类
        Returns: {类别: [(实体, 频次), ...]}
        """
        all_text = ' '.join(self.titles)
        result = {}
        for category, entities in self.ENTITY_DICT.items():
            counter = Counter()
            for entity in entities:
                count = all_text.count(entity)
                if count > 0:
                    counter[entity] = count
            result[category] = counter.most_common(top_n)
        return result

    def find_new_entities(self, high_freq_words, top_n=30):
        """发现新实体（高频词中不在词典里的词）"""
        all_known_entities = set()
        for entities in self.ENTITY_DICT.values():
            all_known_entities.update(entities)
        new_entities = [(word, count) for word, count in high_freq_words
                        if word not in all_known_entities
                        and word not in self.STOPWORDS]
        return new_entities[:top_n]

    def find_related_news(self, keyword, limit=5):
        """查找相关新闻"""
        related = []
        for news in self.news_list:
            if keyword in news['title']:
                related.append(news)
                if len(related) >= limit:
                    break
        return related

    def subdivide_topic(self, topic_name, threshold=30):
        """
        对高频大话题进行细分分析

        Args:
            topic_name: 话题名称（如 'AI', '苹果'）
            threshold: 触发细分的频次阈值

        Returns:
            细分结果字典，包含各子话题的频次和相关新闻
        """
        if topic_name not in self.TOPIC_SUBDIVISIONS:
            return None

        subdivision = self.TOPIC_SUBDIVISIONS[topic_name]
        keywords = subdivision['关键词']

        all_text = ' '.join(self.titles)

        # 统计各子话题频次
        subtopic_counts = Counter()
        for kw in keywords:
            count = all_text.count(kw)
            if count > 0:
                subtopic_counts[kw] = count

        # 为每个子话题找到相关新闻
        subtopic_news = {}
        for kw, count in subtopic_counts.most_common(10):
            subtopic_news[kw] = {
                'count': count,
                'news': self.find_related_news(kw, limit=3)
            }

        return {
            'topic': topic_name,
            'total_count': all_text.count(topic_name),
            'subdivisions': dict(subtopic_counts.most_common(15)),
            'subtopic_news': subtopic_news,
            'dimensions': subdivision['细分维度']
        }

    def analyze(self):
        """执行完整分析"""
        print('=' * 70)
        print('📊 新闻关键词分析报告 v2.0')
        print('=' * 70)
        print(f"新闻总数: {self.data['total']}")
        print(f"来源分布: {self.data['by_source']}")
        print()

        # 方法二：高频词
        print('=' * 70)
        print('📈 方法二：自动提取高频词 TOP30')
        print('=' * 70)
        high_freq_words = self.extract_high_freq_words()
        for i, (word, count) in enumerate(high_freq_words[:30], 1):
            print(f'{i:2}. {word}: {count}次')

        # 方法三：实体分类
        print()
        print('=' * 70)
        print('🏷️ 方法三：实体识别分类')
        print('=' * 70)
        entities = self.extract_entities()
        for category, items in entities.items():
            if items:
                print(f'\n【{category}】TOP10:')
                for name, count in items[:10]:
                    marker = '🔥' if count >= 30 else '  '
                    print(f'  {marker} {name}: {count}次')

        # 🔥 新增：高频大话题细分
        print()
        print('=' * 70)
        print('🔍 高频大话题细分分析（频次≥30自动触发）')
        print('=' * 70)

        for category, items in entities.items():
            for name, count in items:
                if count >= 30 and name in self.TOPIC_SUBDIVISIONS:
                    print(f'\n📌 【{name}】频次过高({count}次)，进行细分分析：')
                    result = self.subdivide_topic(name)
                    if result:
                        print(f'   细分维度: {", ".join(result["dimensions"])}')
                        print(f'   子话题分布:')
                        for sub_kw, sub_count in list(result['subdivisions'].items())[:10]:
                            print(f'     • {sub_kw}: {sub_count}次')

        # 发现新实体
        print()
        print('=' * 70)
        print('🆕 新发现热点（不在词典中）')
        print('=' * 70)
        new_entities = self.find_new_entities(high_freq_words)
        print('\n这些高频词可能是新热点，建议关注:')
        for i, (word, count) in enumerate(new_entities, 1):
            print(f'{i:2}. {word}: {count}次')

        return {
            'high_freq_words': high_freq_words,
            'entities': entities,
            'new_entities': new_entities,
        }

    def generate_topic_report(self, output_file=None):
        """生成选题分析报告"""
        high_freq_words = self.extract_high_freq_words()
        entities = self.extract_entities()
        new_entities = self.find_new_entities(high_freq_words)

        # 构建报告
        report = []
        report.append('# 热点选题分析报告 v2.0\n\n')
        report.append(f'**生成时间**: {self.data["fetch_time"]}\n')
        report.append(f'**新闻总数**: {self.data["total"]} 条\n')
        report.append(f'**来源分布**: {self.data["by_source"]}\n\n')

        # 高频词
        report.append('## 一、高频关键词 TOP30\n\n')
        for i, (word, count) in enumerate(high_freq_words[:30], 1):
            report.append(f'{i:2}. **{word}**: {count}次\n')

        # 实体分类
        report.append('\n## 二、实体分类统计\n\n')
        for category, items in entities.items():
            if items:
                report.append(f'### 【{category}】\n\n')
                for name, count in items[:10]:
                    marker = '🔥' if count >= 30 else ''
                    report.append(f'- {marker} **{name}**: {count}次\n')

        # 🔥 新增：高频大话题细分
        report.append('\n## 三、高频大话题细分分析\n\n')
        report.append('> 当某个话题频次过高（≥30次）时，说明该话题过于宽泛，需要细分。\n\n')

        subdivided_topics = []
        for category, items in entities.items():
            for name, count in items:
                if count >= 30 and name in self.TOPIC_SUBDIVISIONS:
                    result = self.subdivide_topic(name)
                    if result:
                        subdivided_topics.append((name, count, result))

        if subdivided_topics:
            for name, count, result in subdivided_topics:
                report.append(f'### 🔍 {name}（{count}次）→ 细分分析\n\n')
                report.append(f'**细分维度**: {", ".join(result["dimensions"])}\n\n')
                report.append('| 子话题 | 频次 |\n|--------|------|\n')
                for sub_kw, sub_count in list(result['subdivisions'].items())[:10]:
                    report.append(f'| {sub_kw} | {sub_count} |\n')
                report.append('\n')
        else:
            report.append('*本次分析未发现频次过高的大话题*\n\n')

        # 新发现热点
        report.append('## 四、新发现热点（建议关注）\n\n')
        for i, (word, count) in enumerate(new_entities, 1):
            report.append(f'{i:2}. **{word}**: {count}次\n')
            related = self.find_related_news(word, limit=3)
            for news in related:
                report.append(f'   - [{news["source"]}] {news["title"]}\n')

        # 推荐选题
        report.append('\n## 五、推荐选题 TOP15\n\n')
        report.append('> 综合频次、细分热度、话题性推荐\n\n')

        candidates = []

        # 从实体中取
        for category, items in entities.items():
            for name, count in items[:8]:
                if count >= 3:
                    # 如果是大话题，取其子话题
                    if name in self.TOPIC_SUBDIVISIONS:
                        result = self.subdivide_topic(name)
                        if result and result['subdivisions']:
                            for sub_kw, sub_count in list(result['subdivisions'].items())[:3]:
                                if sub_count >= 3:
                                    candidates.append((sub_kw, sub_count, f'{name}细分', category))
                    else:
                        candidates.append((name, count, category, category))

        # 从新热点中取
        for word, count in new_entities[:10]:
            if count >= 4:
                candidates.append((word, count, '新热点', '其他'))

        # 按频次排序
        candidates.sort(key=lambda x: x[1], reverse=True)

        # 去重
        seen = set()
        unique_candidates = []
        for item in candidates:
            if item[0] not in seen:
                seen.add(item[0])
                unique_candidates.append(item)

        for i, (name, count, cat, _) in enumerate(unique_candidates[:15], 1):
            report.append(f'\n### {i}. {name}（{count}次，{cat}）\n\n')
            related = self.find_related_news(name, limit=3)
            for news in related:
                report.append(f'- [{news["source"]}] [{news["title"]}]({news["link"]})\n')

        report_text = ''.join(report)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f'\n✅ 报告已保存: {output_file}')

        return report_text


if __name__ == '__main__':
    import sys

    data_file = 'output/pipeline_output_20260405_231722/crawl_news_result/news_raw.json'
    if len(sys.argv) > 1:
        data_file = sys.argv[1]

    output_file = data_file.replace('news_raw.json', 'topic_analysis.md')

    analyzer = NewsKeywordAnalyzer(data_file)
    analyzer.load_data()
    analyzer.analyze()

    print('\n' + '=' * 70)
    print('📝 生成选题分析报告...')
    print('=' * 70)

    analyzer.generate_topic_report(output_file)