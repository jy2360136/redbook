# 工作流规格说明

## 目标

把“选题 -> 口播稿 -> 配图 -> 分镜 -> HTML -> 视频”做成一条可由 AI 驱动的完整链路。

## 架构

- 主工作流：`.agents/skills/financial-news-video-workflow/`
- HTML 生成：`.agents/skills/frontend-slides/`
- 视频生成：`.agents/skills/remotion/`

## 核心原则

- AI 决定是否调用脚本
- 每步都能暂停、修改、继续
- 状态写入 `workflow_state.json`

## 步骤

1. 新闻抓取与选题
2. 文案撰写
3. 配图提示词与图片准备
4. ASCII 分镜设计
5. HTML 幻灯片生成
6. Remotion 视频导出

## 目录

```text
output/pipeline_output_YYYYMMDD_HHMMSS/
├── workflow_state.json
├── crawl_news_result/
├── manuscript/
├── picture/
├── ascii_draft/
├── html/
└── video/
```

## 旧入口说明

- `run_all_sources.bat`：历史产物
- `check_news.py`：历史产物
- 主目录旧 Python 脚本：不作为当前主入口
