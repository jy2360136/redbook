---
name: financial-news-video-workflow
description: 金融新闻视频制作工作流 - 从新闻爬取到视频生成的完整6步流程。每一步都需要用户确认后才能进入下一步，支持手动修改和调整。
version: 1.0.0
tags: [金融新闻, 视频制作, 工作流, 自动化, B站]
---

# 金融新闻视频制作工作流

**一站式金融新闻视频制作流程**：新闻爬取 → 选题分析 → 文案撰写 → 配图生成 → HTML幻灯片 → 视频导出

## 核心特点

- **交互式工作流**：每一步完成后暂停，等待用户确认或修改
- **状态持久化**：工作流状态保存到文件，支持中断恢复
- **中间文件管理**：所有输出统一存储在带时间戳的目录中

---

## 触发词

| 触发词 | 行为 |
|--------|------|
| `/financial-video` | 启动完整工作流（从 Step 1 开始） |
| `金融新闻视频` | 同上 |
| `财经视频制作` | 同上 |
| `/fv-step 2` | 从指定步骤开始（需已有前置输出） |
| `/fv-continue` | 继续上次中断的工作流 |
| `/fv-status` | 查看当前工作流状态 |

---

## 工作流概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    金融新闻视频制作工作流                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: 新闻爬取                                                │
│  ├─ 执行爬虫脚本                                                 │
│  ├─ 热点分析（出现次数/时效性/视频适配度）                          │
│  └─ ⏸️ 等待用户选择选题                                          │
│                                                                 │
│  Step 2: 文案撰写                                                │
│  ├─ 调用 china-financial-news-writer 技能                        │
│  ├─ 生成初稿                                                    │
│  └─ ⏸️ 等待用户修改确认                                          │
│                                                                 │
│  Step 3: 配图生成                                                │
│  ├─ 分析文案，提取场景                                           │
│  ├─ 生成中英双语图片提示词                                        │
│  └─ ⏸️ 等待用户手动生成图片并放入目录                              │
│                                                                 │
│  Step 4: 布局设计                                                │
│  ├─ 生成分镜规划                                                 │
│  ├─ 生成 ASCII 草图                                              │
│  └─ ⏸️ 等待用户确认布局                                          │
│                                                                 │
│  Step 5: HTML 生成                                               │
│  ├─ 调用 frontend-slides 技能                                    │
│  ├─ 生成 HTML 幻灯片                                             │
│  └─ ⏸️ 等待用户预览确认                                          │
│                                                                 │
│  Step 6: 视频导出                                                │
│  ├─ 调用 remotion 技能                                           │
│  ├─ 生成 Remotion 项目代码                                       │
│  └─ ⏸️ 等待用户渲染视频                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 输出目录结构

每次工作流执行创建一个带时间戳的目录：

```
output/
└── pipeline_output_YYYYMMDD_HHMMSS/
    ├── workflow_state.json              # 工作流状态（用于恢复）
    ├── crawl_news_result/               # Step 1 输出
    │   ├── news_raw.json               # 原始新闻数据
    │   ├── topic_analysis.md           # 选题分析报告
    │   └── selected_topic.json         # 选定选题
    ├── manuscript/                      # Step 2 输出
    │   ├── script_v1.md                # 初稿
    │   ├── script_final.md             # 定稿
    │   └── script_meta.json            # 元数据
    ├── picture/                         # Step 3 输出
    │   ├── prompts.json                # 图片提示词（中英文）
    │   └── images/                     # 用户放置生成的图片
    ├── ascii_draft/                     # Step 4 输出
    │   ├── layout_v1.txt               # 布局草稿
    │   └── layout_final.txt            # 确认布局
    ├── html/                            # Step 5 输出
    │   ├── slides.html                 # 最终 HTML
    │   └── assets/                     # 图片资源
    └── video/                           # Step 6 输出
        ├── project/                    # Remotion 项目
        └── output.mp4                  # 最终视频
```

---

## 详细步骤说明

### Step 1: 新闻爬取与选题分析

**执行内容**：
1. 运行爬虫脚本抓取近3天的财经新闻
2. 统计热点：哪些新闻在多个媒体出现
3. 分析视频适配度：事件复杂度、数据丰富度、故事性
4. 生成选题分析报告

**暂停点**：
- 展示 Top 10 热点选题
- 用户选择一个选题（或手动输入新选题）
- 确认后保存 `selected_topic.json`

**用户操作**：
```
用户: "开始工作流" 或 "/financial-video"
Agent: [执行爬虫] [展示分析报告]
Agent: 请选择一个选题：
       1. 比亚迪Q1销量破50万，新能源车市占率突破40%
       2. 小米汽车SU7正式交付，雷军亲自送车
       3. ...
用户: "我选1" 或 "我想做一个关于xxx的选题"
Agent: [保存选题] Step 1 完成！
       输入 "继续" 进入 Step 2，或先查看/修改选题文件
```

---

### Step 2: 文案撰写

**执行内容**：
1. 读取 `selected_topic.json`
2. 调用 `china-financial-news-writer` 技能
3. 进行深度调研（6维情报网）
4. 生成 B站视频文案初稿

**暂停点**：
- 展示文案初稿
- 用户可以修改 `script_v1.md`
- 确认后保存 `script_final.md`

**用户操作**：
```
Agent: [生成初稿] 文案已生成，请查看：
       manuscript/script_v1.md
       预计时长：12分钟
       字数：3500字
用户: [查看并手动修改文件]
用户: "修改完成，继续"
Agent: [保存定稿] Step 2 完成！
       输入 "继续" 进入 Step 3
```

---

### Step 3: 配图生成

**执行内容**：
1. 分析文案内容，提取关键场景
2. 生成中英双语图片提示词
3. 输出 `prompts.json`

**暂停点**：
- 展示图片提示词列表
- 用户使用提示词在即梦/Midjourney等平台生成图片
- 用户将图片放入 `picture/images/` 目录

**用户操作**：
```
Agent: [生成提示词] 已生成 8 张配图的提示词：
       1. 封面图 - 比亚迪汽车工厂全景
       2. 图1 - 销量数据图表
       3. ...
       请使用这些提示词生成图片，放入 picture/images/ 目录
用户: [手动生图并放入目录]
用户: "图片已准备好，继续"
Agent: [检查目录] 发现 8 张图片
       Step 3 完成！输入 "继续" 进入 Step 4
```

---

### Step 4: 布局设计

**执行内容**：
1. 分析内容结构，生成分镜规划
2. 生成 ASCII 布局草图

**暂停点**：
- 展示 ASCII 草图
- 用户可以调整布局
- 确认后保存 `layout_final.txt`

**用户操作**：
```
Agent: [生成草图]

       ┌─────────────────────────────────────────────────────┐
       │                  开场画面 (00:00-00:30)               │
       ├─────────────────────────────────────────────────────┤
       │                    ┌─────────────┐                  │
       │                    │   50万辆    │                  │
       │                    │ 比亚迪Q1销量 │                  │
       │                    │ [img_001]   │                  │
       │                    └─────────────┘                  │
       └─────────────────────────────────────────────────────┘

       确认此布局？或需要调整？
用户: "把开场画面换成工厂全景，时长改成45秒"
Agent: [修改草图] ...已更新
用户: "确认，继续"
Agent: Step 4 完成！输入 "继续" 进入 Step 5
```

---

### Step 5: HTML 幻灯片生成

**执行内容**：
1. 调用 `frontend-slides` 技能
2. 根据布局和文案生成 HTML

**暂停点**：
- 生成 HTML 文件
- 用户在浏览器预览
- 可以修改 HTML

**用户操作**：
```
Agent: [生成HTML] 已生成 slides.html
       请在浏览器中预览：html/slides.html
用户: [预览并修改]
用户: "预览满意，继续"
Agent: Step 5 完成！输入 "继续" 进入 Step 6
```

---

### Step 6: 视频导出

**执行内容**：
1. 调用 `remotion` 技能
2. 生成 Remotion 项目代码

**暂停点**：
- 用户选择：仅生成代码 / 自动渲染视频

**用户操作**：
```
Agent: [生成Remotion项目] 已生成项目代码
       选择：
       1. 仅生成代码（手动渲染）
       2. 自动渲染视频
用户: "自动渲染"
Agent: [渲染视频] ...已完成
       视频位置：video/output.mp4
       🎉 工作流全部完成！
```

---

## 状态恢复

当用户说 `/fv-continue` 时：

1. 扫描 `output/` 目录，找到最新的 `pipeline_output_*` 文件夹
2. 读取 `workflow_state.json`
3. 从 `current_step` 继续执行

**状态文件格式**：
```json
{
  "workflow_id": "pipeline_output_20260405_143000",
  "created_at": "2026-04-05T14:30:00",
  "current_step": 3,
  "completed_steps": [1, 2],
  "step_status": {
    "step1": {"status": "completed", "completed_at": "..."},
    "step2": {"status": "completed", "completed_at": "..."},
    "step3": {"status": "in_progress", "started_at": "..."}
  },
  "config": {
    "days": 3,
    "sources": "all",
    "video_style": "深度分析",
    "target_platform": "B站"
  }
}
```

---

## 依赖技能

| 技能 | 用途 | 步骤 |
|------|------|------|
| `china-financial-news-writer` | 金融新闻写作 | Step 2 |
| `article-illustration-generator` | 图片提示词生成 | Step 3 |
| `frontend-slides` | HTML 幻灯片生成 | Step 5 |
| `remotion` | 视频生成 | Step 6 |

---

## 脚本文件

| 脚本 | 用途 |
|------|------|
| `scripts/crawl_news.py` | 新闻爬虫（虎嗅、36氪、钛媒体、界面） |
| `scripts/crawl_community.py` | 社区讨论爬虫（雪球、知乎） |

---

## 参考文档

| 文档 | 用途 |
|------|------|
| `references/topic-analysis-framework.md` | 选题分析框架 |
| `references/event-news-template.md` | 事件新闻写作模板 |
| `references/ascii-draft-guide.md` | ASCII 草图设计指南 |
| `references/prompt-templates.md` | 中英双语图片提示词模板 |