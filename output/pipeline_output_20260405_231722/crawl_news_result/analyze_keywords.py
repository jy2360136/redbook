# -*- coding: utf-8 -*-
"""
新闻关键词分析工具 - 方法二 + 方法三 组合使用
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
            # 科技创业者
            '董宇辉', '特朗普', '马斯克', '雷军', '罗永浩',
            '周鸿祎', '俞敏洪', '李佳琦', '薇娅', '罗翔', '张一鸣',
            '马云', '马化腾', '刘强东', '王兴', '黄峥', '李想', '李斌',
            # 其他
            '巴菲特', '孙正义', '黄仁勋', '张雪', '全红婵',
        },
        '地点': {
            # 国家
            '美国', '中国', '伊朗', '巴基斯坦', '以色列', '俄罗斯', '乌克兰',
            '日本', '韩国', '印度', '德国', '英国', '法国',
            # 城市
            '北京', '上海', '深圳', '广州', '杭州', '武汉', '成都', '重庆',
            '南京', '苏州', '西安', '长沙', '郑州', '川渝',
            # 地区
            '欧洲', '中东', '东南亚', '北美', '非洲',
        },
        '行业': {
            # 热门赛道
            'AI', '人工智能', '新能源', '电动车', '芯片', '半导体',
            '互联网', '电商', '直播', '外卖', '游戏', '电影',
            '房地产', '医疗', '教育', '金融', '元宇宙',
            # 细分领域
            '无人驾驶', '自动驾驶', '萝卜快跑', 'ChatGPT', '大模型',
            'AIGC', 'SaaS', '机器人', '人形机器人',
        },
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

        Returns:
            [(词, 频次), ...]
        """
        all_text = ' '.join(self.titles)

        # 正则提取中文词组
        words = re.findall(r'[\u4e00-\u9fa5]{2,8}', all_text)

        # 过滤
        filtered_words = [w for w in words
                          if w not in self.STOPWORDS
                          and len(w) >= min_length]

        # 统计
        word_freq = Counter(filtered_words)

        # 返回TOP N
        return word_freq.most_common(top_n)

    def extract_entities(self, top_n=15):
        """
        方法三：实体识别分类

        Returns:
            {类别: [(实体, 频次), ...]}
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
        """
        发现新实体（高频词中不在词典里的词）

        Returns:
            [(词, 频次), ...] 新发现的实体
        """
        # 合并所有已知实体
        all_known_entities = set()
        for entities in self.ENTITY_DICT.values():
            all_known_entities.update(entities)

        # 找出高频词中不在词典的
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

    def analyze(self):
        """执行完整分析"""
        print('=' * 70)
        print('📊 新闻关键词分析报告')
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
                    print(f'  • {name}: {count}次')

        # 发现新实体
        print()
        print('=' * 70)
        print('🔍 新发现热点（不在词典中）')
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
        report.append('# 热点选题分析报告\n')
        report.append(f'**生成时间**: {self.data["fetch_time"]}\n')
        report.append(f'**新闻总数**: {self.data["total"]} 条\n')
        report.append(f'**来源分布**: {self.data["by_source"]}\n\n')

        # 高频词
        report.append('## 一、高频关键词 TOP30\n')
        for i, (word, count) in enumerate(high_freq_words[:30], 1):
            report.append(f'{i:2}. **{word}**: {count}次\n')

        # 实体分类
        report.append('\n## 二、实体分类统计\n')
        for category, items in entities.items():
            if items:
                report.append(f'\n### 【{category}】\n')
                for name, count in items[:10]:
                    report.append(f'- {name}: {count}次\n')

        # 新发现热点
        report.append('\n## 三、新发现热点（建议关注）\n')
        for i, (word, count) in enumerate(new_entities, 1):
            report.append(f'{i:2}. **{word}**: {count}次\n')
            # 添加相关新闻
            related = self.find_related_news(word, limit=3)
            for news in related:
                report.append(f'   - [{news["source"]}] {news["title"]}\n')

        report.append('\n## 四、推荐选题 TOP10\n')
        # 综合评分推荐选题
        # 1. 从实体中找出高频的
        # 2. 结合新发现热点
        # 3. 给出相关新闻

        # 合并所有候选
        candidates = []

        # 从实体中取
        for category, items in entities.items():
            for name, count in items[:5]:
                if count >= 3:
                    candidates.append((name, count, category))

        # 从新热点中取
        for word, count in new_entities[:10]:
            if count >= 5:
                candidates.append((word, count, '新热点'))

        # 按频次排序
        candidates.sort(key=lambda x: x[1], reverse=True)

        for i, (name, count, cat) in enumerate(candidates[:10], 1):
            report.append(f'\n### {i}. {name}（{count}次，{cat}）\n')
            related = self.find_related_news(name, limit=3)
            for news in related:
                report.append(f'- [{news["source"]}] [{news["title"]}]({news["link"]})\n')

        report_text = ''.join(report)

        # 保存文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f'\n报告已保存: {output_file}')

        return report_text


if __name__ == '__main__':
    import sys

    # 默认数据文件
    data_file = 'output/pipeline_output_20260405_231722/crawl_news_result/news_raw.json'

    # 命令行参数
    if len(sys.argv) > 1:
        data_file = sys.argv[1]

    # 输出文件
    output_file = data_file.replace('news_raw.json', 'topic_analysis.md')

    # 运行分析
    analyzer = NewsKeywordAnalyzer(data_file)
    analyzer.load_data()
    analyzer.analyze()

    print('\n' + '=' * 70)
    print('📝 生成选题分析报告...')
    print('=' * 70)

    analyzer.generate_topic_report(output_file)