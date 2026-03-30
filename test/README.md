# 测试文件说明

本目录包含项目的测试和调试脚本。

## 📋 测试文件列表

### ✅ 保留的测试文件（重要）

1. **test_main_integration.py**
   - 用途：测试主程序整合情况
   - 功能：验证标题格式、文件输出规范、字段完整性等
   - 运行：`python test/test_main_integration.py`

2. **test_jiemian_full.py**
   - 用途：完整测试界面新闻爬虫
   - 功能：测试 API 抓取、时间过滤、分页加载等
   - 运行：`python test/test_jiemian_full.py`

3. **test_tmtpost.py**
   - 用途：测试钛媒体视频过滤功能
   - 功能：验证视频新闻是否被正确过滤
   - 运行：`python test/test_tmtpost.py`

### ❌ 已删除的文件（临时调试用）

以下文件为开发过程中的临时调试脚本，已删除：

- `test_36kr_api.py` - 36 氪 API 拦截测试（临时调试）
- `test_jiemian.py` - 界面新闻 HTML 结构测试（临时调试）
- `test_jiemian_api.py` - 界面新闻 JSONP 解析测试（临时调试）
- `test_time_parse.py` - 时间解析函数测试（临时调试）
- `test_timedelta.py` - timedelta 测试（临时调试）

## 🔧 使用说明

### 运行所有测试

```bash
cd test
python test_main_integration.py
python test_jiemian_full.py
python test_tmtpost.py
```

### 依赖安装

```bash
pip install -r ../requirements.txt
playwright install chromium
```

## 📝 说明

- 测试文件统一存放在 `test/` 目录下，保持项目根目录整洁
- 临时调试脚本应及时清理，避免混淆
- 重要的测试脚本应保留并维护，用于回归测试
