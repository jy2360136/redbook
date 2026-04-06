# Step 2: 文案撰写

## 执行流程

### 2.1 读取选题信息

读取 Step 1 的输出：
```
output/pipeline_output_xxx/crawl_news_result/selected_topic.json
output/pipeline_output_xxx/crawl_news_result/news_raw.json
```

### 2.2 调用写作技能

调用 `china-financial-news-writer` 技能，根据选题类型选择框架：

**选题类型判断**：
| 类型 | 判断依据 | 使用框架 |
|------|----------|----------|
| 财报分析 | 包含"财报"、"Q1/Q2/Q3/Q4"、"营收"、"利润" | tech-giant.md / ev-maker.md |
| 产品发布 | 包含"发布"、"上市"、"新品"、"交付" | event-news-template.md |
| 人事变动 | 包含"离职"、"上任"、"高管"、"CEO" | event-news-template.md |
| 政策影响 | 包含"政策"、"监管"、"新规"、"补贴" | event-news-template.md |
| 市场事件 | 包含"股价"、"市值"、"涨跌"、"暴跌" | event-news-template.md |

### 2.3 深度调研

执行 6 维情报搜集（参考 `china-financial-news-writer/references/deep-research.md`）：

1. **新闻媒体报道**：虎嗅、36氪、财新、界面
2. **视频平台内容**：B站、抖音相关视频
3. **社交媒体讨论**：微博、小红书
4. **投资社区/论坛**：雪球、东方财富股吧
5. **官方信息源**：公司官网、交易所公告
6. **数据工具**：百度指数、天眼查

### 2.4 生成文案初稿

生成 B站视频文案，格式参考：

```markdown
# [标题]

> 预计时长：12分钟 | 字数：3500字

## 开场钩子（30秒）

[数据冲击/悬念设置/热点切入]

---

## 事件概述（1-2分钟）

[时间线 + 核心事实 + 市场反应]

---

## 深度分析（5-8分钟）

### 维度一：[标题]

[分析内容]

### 维度二：[标题]

[分析内容]

### 维度三：[标题]

[分析内容]

---

## 历史对比（2-3分钟）

[对比案例/历史事件]

---

## 未来展望（1-2分钟）

[趋势判断/关键观察点]

---

## 结尾互动（30秒）

[总结 + 引导互动]

---

## 数据来源

- [来源1]
- [来源2]

---
*调研 & 撰写：AI（Claude）*
*主导 & 审校：[用户名]*
```

### 2.5 保存初稿

保存到：
```
output/pipeline_output_xxx/manuscript/script_v1.md
output/pipeline_output_xxx/manuscript/script_meta.json
```

**元数据文件**：
```json
{
  "created_at": "2026-04-05T14:40:00",
  "estimated_duration_minutes": 12,
  "word_count": 3500,
  "style": "深度分析",
  "target_platform": "B站",
  "source_news_count": 5,
  "research_depth": "full"
}
```

### 2.6 用户修改确认

**暂停等待**：
- 展示文案预览（标题、时长、字数）
- 告知文件位置
- 用户可以手动修改

**用户操作**：
```
Agent: 文案初稿已生成！
       📄 位置：manuscript/script_v1.md
       ⏱️ 预计时长：12分钟
       📝 字数：3500字

       请查看并修改文案，修改完成后回复"继续"

用户: [查看并修改文件]
用户: 修改完成，继续
```

### 2.7 保存定稿

用户确认后，复制为定稿：
```
script_v1.md → script_final.md
```

更新状态文件：
```json
{
  "current_step": 2,
  "completed_steps": [1, 2],
  "step_status": {
    "step1": {"status": "completed"},
    "step2": {"status": "completed", "final_word_count": 3800}
  }
}
```

---

## 完成标准

Step 2 完成标志：
- ✅ `script_v1.md` 已生成
- ✅ `script_meta.json` 已保存
- ✅ 用户已确认修改
- ✅ `script_final.md` 已保存
- ✅ `workflow_state.json` 已更新

---

## 恢复检查点

如果用户说 `/fv-continue`，检查：
1. `script_final.md` 是否存在
2. 如果存在，直接进入 Step 3
3. 如果只有 `script_v1.md`，提示用户确认定稿