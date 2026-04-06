# Step 5: HTML 幻灯片生成

## 执行流程

### 5.1 读取输入

读取之前步骤的输出：
```
output/pipeline_output_xxx/manuscript/script_final.md    # 文案
output/pipeline_output_xxx/picture/images/               # 图片
output/pipeline_output_xxx/ascii_draft/layout_final.txt  # 布局
```

### 5.2 调用 frontend-slides 技能

根据布局文件生成 HTML 幻灯片。

**关键参数**：
- 目标平台：B站（16:9 竖版视频）
- 主题风格：根据文案主题选择
- 动画效果：简洁专业
- 字体：中文使用思源黑体/霞鹜文楷

### 5.3 HTML 生成规范

**遵循 frontend-slides 的核心原则**：
1. Zero Dependencies - 单文件 HTML，无外部依赖
2. Viewport Fitting - 每页适配 100vh，无滚动
3. Responsive - 使用 clamp() 实现响应式字体

**幻灯片结构**：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>比亚迪Q1销量破50万</title>
    <style>
        /* 从 frontend-slides/viewport-base.css 引入基础样式 */
        /* ... */
    </style>
</head>
<body>
    <div class="slide" id="slide-01">
        <!-- 开场封面 -->
    </div>
    <div class="slide" id="slide-02">
        <!-- 数据冲击 -->
    </div>
    <!-- ... 更多幻灯片 -->
</body>
</html>
```

### 5.4 复制图片资源

将图片复制到 HTML 资源目录：
```
picture/images/* → html/assets/
```

更新 HTML 中的图片路径：
```
../picture/images/img_001.png → assets/img_001.png
```

### 5.5 生成 HTML 文件

保存到：
```
output/pipeline_output_xxx/html/slides.html
output/pipeline_output_xxx/html/assets/img_001.png
output/pipeline_output_xxx/html/assets/img_002.png
...
```

### 5.6 用户预览确认

**暂停等待**：
- 生成 HTML 文件
- 用户在浏览器预览

**用户操作**：
```
Agent: HTML 幻灯片已生成！
       📄 位置：html/slides.html

       预览方式：
       1. 在浏览器中打开 html/slides.html
       2. 按 F11 全屏查看效果
       3. 使用方向键翻页

       预览完成后：
       - 如果需要修改，输入具体修改要求
       - 如果满意，输入"继续"进入视频生成

用户: [浏览器预览]
用户: 把第二页的字体改大一点
Agent: [修改HTML] ...已更新

用户: 继续预览...满意了，继续
Agent: Step 5 完成！输入"继续"进入 Step 6
```

---

## 完成标准

Step 5 完成标志：
- ✅ `slides.html` 已生成
- ✅ 图片资源已复制到 `assets/`
- ✅ 用户已预览确认
- ✅ `workflow_state.json` 已更新

---

## 样式预设

可选的主题风格：

| 风格名称 | 配色 | 适用场景 |
|----------|------|----------|
| 商务蓝 | 深蓝 + 白 + 金 | 财经新闻、企业报道 |
| 科技黑 | 黑色 + 蓝紫渐变 | 科技新闻、产品发布 |
| 新闻白 | 白色 + 红 + 黑 | 重大新闻、突发事件 |
| 暖色调 | 米色 + 橙 + 褐 | 人文故事、人物访谈 |

---

## 恢复检查点

如果用户说 `/fv-continue`，检查：
1. `slides.html` 是否存在
2. 如果存在，直接进入 Step 6
3. 如果不存在，重新生成