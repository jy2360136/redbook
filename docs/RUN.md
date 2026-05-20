# 运行说明

当前仓库以 Skills 为主入口。

## 主入口

- `.agents/skills/financial-news-video-workflow/SKILL.md`
- 触发词：`/financial-video`、`金融新闻视频`、`财经视频制作`

## Step 5 / Step 6

- Step 5：`.agents/skills/frontend-slides/SKILL.md`
- Step 6：`.agents/skills/remotion/SKILL.md`

## 继续流程

- 找最新的 `output/pipeline_output_*/workflow_state.json`
- 读取 `current_step`
- 按步骤继续

## 不再推荐

- `run_all_sources.bat`
- `check_news.py`
- 主目录旧 Python 入口
