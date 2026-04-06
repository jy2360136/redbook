# Step 6: 视频导出

## 执行流程

### 6.1 读取输入

读取之前步骤的输出：
```
output/pipeline_output_xxx/html/slides.html           # HTML幻灯片
output/pipeline_output_xxx/html/assets/               # 图片资源
output/pipeline_output_xxx/ascii_draft/layout_final.txt  # 时长信息
```

### 6.2 调用 remotion 技能

根据 HTML 幻灯片生成 Remotion 项目代码。

**Remotion 项目结构**：
```
output/pipeline_output_xxx/video/project/
├── src/
│   ├── index.ts                    # 入口文件
│   ├── compositions/
│   │   └── MainVideo.tsx           # 主视频组件
│   ├── components/
│   │   ├── Slide01.tsx             # 各幻灯片组件
│   │   ├── Slide02.tsx
│   │   └── ...
│   └── assets/
│       ├── img_001.png
│       └── ...
├── package.json
├── tsconfig.json
└── remotion.config.ts
```

### 6.3 生成 Remotion 代码

**主要配置**：
```typescript
// src/index.ts
import { registerRoot } from "remotion";
import { VideoComposition } from "./compositions/MainVideo";

registerRoot(VideoComposition);

// src/compositions/MainVideo.tsx
import { Composition } from "remotion";
import { Slide01, Slide02, ... } from "../components";

export const VideoComposition: React.FC = () => {
  return (
    <Composition
      id="MainVideo"
      component={MainVideo}
      durationInFrames={21600}  // 12分钟 * 30fps = 21600帧
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

**每个幻灯片组件示例**：
```typescript
// src/components/Slide01.tsx
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

export const Slide01: React.FC = () => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a3328" }}>
      <img
        src="../assets/img_001.png"
        style={{ opacity }}
      />
      <h1 style={{ opacity }}>
        比亚迪Q1销量破50万
      </h1>
    </AbsoluteFill>
  );
};
```

### 6.4 用户选择渲染方式

**暂停等待**：
- 用户选择渲染方式

**选项**：
```
Agent: Remotion 项目代码已生成！
       📁 位置：video/project/

       请选择：
       1. 仅生成代码（手动渲染）
          - 需要自行安装 Node.js 和 Remotion
          - 运行：cd video/project && npm install && npx remotion render

       2. 自动渲染视频（需要安装 Remotion）
          - 我将自动执行渲染命令
          - 输出：video/output.mp4

用户: 2
Agent: [开始渲染] ...这可能需要几分钟
```

### 6.5 渲染视频（可选）

如果用户选择自动渲染：

```bash
cd output/pipeline_output_xxx/video/project
npm install
npx remotion render MainVideo out/video.mp4
```

### 6.6 工作流完成

```
Agent: 🎉 工作流全部完成！

       📊 工作流总结：
       ┌──────────────────────────────────────────────────┐
       │ Step 1: 新闻爬取           ✅ 完成               │
       │ Step 2: 文案撰写           ✅ 完成               │
       │ Step 3: 配图生成           ✅ 完成               │
       │ Step 4: 布局设计           ✅ 完成               │
       │ Step 5: HTML生成           ✅ 完成               │
       │ Step 6: 视频导出           ✅ 完成               │
       └──────────────────────────────────────────────────┘

       📁 输出文件：
       • 视频文件：video/output.mp4
       • HTML幻灯片：html/slides.html
       • 文案定稿：manuscript/script_final.md
       • 配图文件：picture/images/ (8张)

       📈 统计：
       • 总时长：约12分钟
       • 幻灯片：15张
       • 配图：8张
       • 字数：3800字

       感谢使用金融新闻视频工作流！
```

---

## 完成标准

Step 6 完成标志：
- ✅ Remotion 项目代码已生成
- ✅ 用户已选择渲染方式
- ✅ （如果选择自动渲染）视频已输出
- ✅ `workflow_state.json` 已更新为完成状态

---

## 恢复检查点

如果用户说 `/fv-continue`，检查：
1. Remotion 项目是否存在
2. 是否已渲染视频
3. 如果只生成了代码，提示用户选择渲染方式