# Step 1: 新闻爬取与选题分析

## 执行流程

### 1.1 创建工作流目录

```bash
# 创建带时间戳的工作流目录
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p output/pipeline_output_${timestamp}/{crawl_news_result,manuscript,picture/images,ascii_draft,html/assets,video/project}

# 创建状态文件
cat > output/pipeline_output_${timestamp}/workflow_state.json << EOF
{
  "workflow_id": "pipeline_output_${timestamp}",
  "created_at": "$(date -Iseconds)",
  "current_step": 1,
  "completed_steps": [],
  "step_status": {},
  "config": {}
}
EOF
```

### 1.2 执行爬虫脚本

```bash
python scripts/crawl_news.py --days 3 --sources all
```

**支持的新闻源**：
- `huxiu`: 虎嗅网
- `36kr`: 36氪
- `tmtpost`: 钛媒体
- `jiemian`: 界面新闻

**可选参数**：
- `--days N`: 抓取最近 N 天的新闻（默认 3）
- `--sources huxiu,36kr`: 只抓取指定来源
- `--filter-companies`: 只保留包含公司名的新闻

### 1.3 热点分析

爬取完成后，对新闻进行热点分析：

**分析维度**：
1. **出现频次**：同一事件在多个媒体出现的次数
2. **时效性**：发布时间距离现在多久
3. **影响力**：媒体权重（虎嗅/36氪权重更高）
4. **视频适配度**：评估是否适合做深度视频
   - 事件复杂度：是否有足够的背景故事
   - 数据丰富度：是否有可可视化的数据
   - 故事性：是否有戏剧性转折

**分析输出**（保存到 `topic_analysis.md`）：

```markdown
# 选题分析报告

## 热点排行

| 排名 | 选题 | 出现次数 | 时效性 | 影响力 | 视频适配度 | 综合评分 |
|------|------|----------|--------|--------|------------|----------|
| 1 | 比亚迪Q1销量破50万 | 4 | ★★★★★ | ★★★★☆ | ★★★★★ | 95 |
| 2 | 小米SU7正式交付 | 3 | ★★★★☆ | ★★★★★ | ★★★★☆ | 88 |
| ... | ... | ... | ... | ... | ... | ... |

## 推荐选题详细分析

### 选题1：比亚迪Q1销量破50万

**事件概述**：比亚迪公布Q1销量数据，突破50万辆...

**视频适配度分析**：
- ✅ 数据丰富：有销量、市占率、同比环比等多个数据点
- ✅ 故事性强：从被质疑到全球第一的逆袭之路
- ✅ 可视化空间：销量走势图、市场份额饼图
- ⚠️ 注意事项：需标注数据来源，避免投资建议

**建议切入点**：
1. 数据冲击开场：50万辆意味着什么
2. 历史对比：3年前比亚迪是什么样
3. 行业格局：新能源车市占率突破40%
4. 未来展望：能否持续领跑
```

### 1.4 用户选择选题

**暂停等待**：
- 展示 Top 10 热点选题
- 用户可以：
  - 输入数字选择推荐选题
  - 手动输入新的选题

**保存选题**（`selected_topic.json`）：

```json
{
  "selected_at": "2026-04-05T14:35:00",
  "topic": "比亚迪Q1销量破50万，新能源车市占率突破40%",
  "source_news": [
    {"title": "...", "source": "虎嗅", "link": "..."},
    {"title": "...", "source": "36氪", "link": "..."}
  ],
  "analysis": {
    "occurrence_count": 4,
    "video_suitability": "high",
    "suggested_angle": "数据冲击开场"
  }
}
```

### 1.5 完成标准

Step 1 完成标志：
- ✅ `news_raw.json` 已生成
- ✅ `topic_analysis.md` 已生成
- ✅ 用户已选择选题
- ✅ `selected_topic.json` 已保存
- ✅ `workflow_state.json` 已更新

---

## 恢复检查点

如果用户说 `/fv-continue`，检查：
1. `selected_topic.json` 是否存在
2. 如果存在，直接进入 Step 2
3. 如果不存在，重新执行选题选择