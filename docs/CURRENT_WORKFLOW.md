# 当前工作流说明（Skills 版）

这套项目现在已经切到“AI 调用 Skill 为主”的运行方式，不再依赖主目录里的独立 Python 入口来串完整流程。

## 最近改动

- 删除了旧的独立入口脚本思路，保留 Skill 作为主入口。
- 安装了 `frontend-slides` Skill 到 `.agents/skills/frontend-slides/`。
- Step 5 已改为调用 `frontend-slides` 生成 `html/slides.html`。
- Step 6 已改为调用 `remotion` 生成 `video/output.mp4`。
- 图片只保留一份主源：`output/pipeline_output_*/picture/images/`，其他位置只引用，不再复制。
- 已清理掉不再需要的分析脚本：
  - `run_all_sources.bat`
  - `check_news.py`
  - `output/.../crawl_news_result/analyze_keywords.py`
  - `news_output/analyze_news_keywords.py`

## 工作流怎么运转

1. 通过 `/financial-video` 或“金融新闻视频”触发工作流。
2. AI 读取 `output/pipeline_output_*/workflow_state.json`，判断当前停在哪一步。
3. Step 1 到 Step 4 负责：
   - 抓新闻
   - 选题
   - 写口播稿
   - 生成图片提示词
   - 输出 ASCII 分镜
4. Step 5 负责：
   - 由 `frontend-slides` 生成 HTML 幻灯片
   - 浏览器里预览 `html/slides.html`
5. Step 6 负责：
   - 由 `remotion` 生成视频工程
   - 渲染出 `video/output.mp4`

## 当前推荐入口

- 主流程：`.agents/skills/financial-news-video-workflow/SKILL.md`
- Step 5：`.agents/skills/frontend-slides/SKILL.md`
- Step 6：`.agents/skills/remotion/SKILL.md`

## 当前输出示例

- HTML：`output/pipeline_output_20260405_231722/html/slides.html`
- 视频：`output/pipeline_output_20260405_231722/video/output.mp4`
- 状态：`output/pipeline_output_20260405_231722/workflow_state.json`

## 继续工作时怎么判断进度

- 看 `workflow_state.json` 的 `current_step`
- 看 `completed_steps`
- 看 `step_status.stepN.output`

## 备注

- 如果 HTML 里只看到图片、看不到文字，优先检查浏览器控制台是否有脚本报错。
- 如果视频渲染报图片 404，优先检查 Remotion 里是否使用了 `staticFile('assets/...')`。
