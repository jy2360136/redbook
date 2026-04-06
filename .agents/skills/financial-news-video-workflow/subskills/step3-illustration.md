# Step 3: 配图生成

## 执行流程

### 3.1 读取文案

读取 Step 2 的输出：
```
output/pipeline_output_xxx/manuscript/script_final.md
```

### 3.2 提取场景

分析文案结构，提取适合配图的场景：

**场景提取规则**：
1. **封面图**：基于标题和核心主题
2. **数据图**：文案中提到的关键数据
3. **人物/事件图**：文案中涉及的人物或事件
4. **场景图**：文案描述的场景
5. **对比图**：历史对比或竞品对比
6. **结尾图**：总结或展望配图

**场景数量建议**：
- 5分钟视频：4-6张图
- 10分钟视频：8-12张图
- 15分钟视频：12-18张图

### 3.3 生成提示词

为每个场景生成中英双语提示词，保存到 `prompts.json`：

```json
{
  "generated_at": "2026-04-05T14:50:00",
  "total_prompts": 8,
  "style": "现代商务风格",
  "prompts": [
    {
      "id": 1,
      "scene": "封面",
      "timecode": "00:00",
      "chinese": "比亚迪汽车工厂鸟瞰图，现代化生产线，蓝色科技感光效，商务风格",
      "english": "Aerial view of BYD automobile factory, modern production line, blue technology lighting effect, business style, professional, 16:9"
    },
    {
      "id": 2,
      "scene": "销量数据",
      "timecode": "00:30",
      "chinese": "汽车销量柱状图，比亚迪品牌，蓝色和金色配色，数据可视化风格，简洁商务",
      "english": "Car sales bar chart, BYD brand, blue and gold color scheme, data visualization style, clean business, 16:9"
    },
    {
      "id": 3,
      "scene": "市场份额",
      "timecode": "02:00",
      "chinese": "新能源汽车市场份额饼图，比亚迪占40%，其他品牌分块，3D立体效果",
      "english": "New energy vehicle market share pie chart, BYD occupies 40%, other brands in segments, 3D effect, professional, 16:9"
    }
  ]
}
```

### 3.4 提示词模板

参考 `references/prompt-templates.md` 中的模板：

**通用模板**：
```
中文：[主体描述]，[场景/背景]，[风格]，[色调]
English: [Subject description], [Scene/Background], [Style], [Color tone], professional, 16:9
```

**风格选项**：
- 商务风格：clean business, professional
- 科技风格：technology, futuristic, neon
- 新闻风格：news broadcast, journalistic
- 信息图表：infographic, data visualization
- 手绘风格：hand-drawn, illustration

### 3.5 创建图片目录

```
output/pipeline_output_xxx/picture/
├── prompts.json        # 提示词文件
└── images/             # 用户放置生成的图片
    ├── img_001.png     # 封面图
    ├── img_002.png     # 数据图1
    ├── img_003.png     # 数据图2
    └── ...
```

### 3.6 用户手动生图

**暂停等待**：
- 展示提示词列表
- 告知用户操作步骤

**用户操作指引**：
```
Agent: 已生成 8 张配图的提示词！

       📄 提示词文件：picture/prompts.json

       使用方法：
       1. 打开即梦/Midjourney等生图网站
       2. 复制对应的英文提示词
       3. 生成图片后下载
       4. 将图片放入 picture/images/ 目录
       5. 按顺序命名：img_001.png, img_002.png...

       提示词预览：
       ┌──────────────────────────────────────────────────┐
       │ 1. 封面 (00:00)                                   │
       │    Aerial view of BYD automobile factory...      │
       ├──────────────────────────────────────────────────┤
       │ 2. 销量数据 (00:30)                               │
       │    Car sales bar chart, BYD brand...             │
       └──────────────────────────────────────────────────┘

       生成完成后回复"继续"

用户: [手动生图并放入目录]
用户: 图片已准备好，继续
```

### 3.7 检查图片

用户确认后，检查图片目录：
```
统计 picture/images/ 目录下的图片数量
与 prompts.json 中的数量对比
如果数量匹配，进入下一步
如果不匹配，提示缺少哪些图片
```

---

## 完成标准

Step 3 完成标志：
- ✅ `prompts.json` 已生成
- ✅ `images/` 目录已创建
- ✅ 图片数量与提示词匹配
- ✅ `workflow_state.json` 已更新

---

## 恢复检查点

如果用户说 `/fv-continue`，检查：
1. `prompts.json` 是否存在
2. `images/` 目录是否有图片
3. 图片数量是否匹配
4. 如果不匹配，提示缺少的图片编号