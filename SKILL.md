---
name: zzgz-autoto-core
description: 多平台自动化核心库，为小红书、微信公众号等平台发布提供基础能力
version: 1.0.0
author: zzgz
tags: [automation, core, library, wechat, xhs]
---

# Zzgz Autoto Core

多平台自动化核心库，为小红书、微信公众号等平台发布提供基础能力。

## 说明

⚠️ **这不是一个独立使用的 Skill**，而是被其他 Skill 依赖的核心库。

依赖本核心的 Skill：
- `zzgz-autoto-xhs` - 小红书自动发布
- `zzgz-autoto-wechat` - 微信公众号自动发布

## 核心模块

### `core/data.py`
数据处理工具
- `is_url()` - 判断字符串是否为 URL
- `load_article_payload()` - 从 JSON 加载文章数据
- `save_article_payload()` - 保存文章数据到 JSON
- `ensure_test_placeholder()` - 确保测试占位图存在

### `core/image_utils.py`
图片处理工具
- `download_image()` - 从 URL 下载图片
- `search_and_download_cover()` - 从百度图片搜索封面
- `get_default_cover()` - 生成默认封面图片

### `core/ui.py`
UI 交互工具
- `_ui_settle()` - 等待界面稳定
- `_fill_richtext()` - 富文本编辑器输入（支持 ProseMirror/Tiptap、Quill）

### `core/platform_config.py`
平台配置管理
- `PlatformConfig` - 平台完整配置数据类
- `PlatformLimits` - 平台限制配置（标题长度、图片数量等）
- `PlatformFeatures` - 平台功能特性（API支持、草稿支持等）
- `get_platform_config()` - 获取平台配置
- `list_supported_platforms()` - 列出所有支持的平台

### `sources/wechat.py`
微信公众号文章抓取
- `scrape_article()` - 抓取微信文章内容、标题、图片

### `utils/_shared.py`
共享工具函数
- `get_skill_dir()` - 获取 skill 目录
- `get_data_dir()` - 获取数据目录
- `get_auth_state_path()` - 获取登录态文件路径
- `process_image_paths()` - 处理图片路径
- `resolve_cover_image()` - 解析封面图片

### `utils/openclaw_messaging.py`
OpenClaw 消息发送工具
- `OpenClawMessenger` - 消息发送器类
  - `__init__(channel, target, account, session_key)` - 初始化
  - `from_env()` - 从环境变量创建
  - `from_inbound_meta()` - 从 Inbound Context 创建
  - `send_text()` / `send_text_safe()` - 发送文本
  - `send_image()` / `send_image_safe()` - 发送图片
- `OpenClawNotifier` - 通知器类
- `send_notification()` - 快速发送通知

## 目录结构

```
zzgz-autoto-core/
├── zzgz_autoto_core/         # 主包目录
│   ├── __init__.py           # 包入口，导出公共接口
│   ├── core/                 # 核心模块
│   │   ├── __init__.py
│   │   ├── data.py           # 数据处理
│   │   ├── image_utils.py    # 图片处理
│   │   ├── ui.py             # UI交互
│   │   └── platform_config.py # 平台配置
│   ├── sources/              # 内容源抓取
│   │   ├── __init__.py
│   │   └── wechat.py         # 微信公众号抓取
│   └── utils/                # 工具函数
│       ├── __init__.py
│       └── _shared.py        # 共享工具
├── pyproject.toml            # 包配置
└── README.md
```

## 依赖

```
playwright
pillow
requests
```

## 使用方式（被其他 Skill 依赖）

### 安装

```bash
pip install git+https://github.com/henryczq/zzgz-autoto-core.git@master
```

### 导入使用

```python
# 方式1: 直接从包导入
from zzgz_autoto_core.core.data import load_article_payload
from zzgz_autoto_core.core.image_utils import download_image
from zzgz_autoto_core.core.platform_config import get_platform_config

# 方式2: 从包根导入（推荐）
from zzgz_autoto_core import load_article_payload, download_image, get_platform_config

# 获取平台配置
config = get_platform_config("xhs")
print(f"标题限制: {config.limits.title_max_length}")
```

### OpenClawMessenger 使用示例

```python
from zzgz_autoto_core.utils.openclaw_messaging import OpenClawMessenger, OpenClawNotifier

# 方式1: 直接传入参数
messenger = OpenClawMessenger(
    channel="telegram",
    target="telegram:5747692163",
    account="8606699467"  # 可选
)
messenger.send_text("Hello!")

# 方式2: 从环境变量读取
# export OPENCLAW_CHANNEL=telegram
# export OPENCLAW_TARGET=telegram:5747692163
# export OPENCLAW_ACCOUNT=8606699467
messenger = OpenClawMessenger.from_env()
messenger.send_text("自动读取配置")

# 方式3: 从 OpenClaw Inbound Context (trusted metadata) 读取
inbound_meta = {
    "schema": "openclaw.inbound_meta.v1",
    "chat_id": "telegram:5747692163",      # -> target
    "account_id": "8606699467",              # -> account (可选)
    "channel": "telegram",
    "provider": "telegram",
    "surface": "telegram",
    "chat_type": "direct"
}
messenger = OpenClawMessenger.from_inbound_meta(inbound_meta)
messenger.send_text("从 Inbound Context 读取")

# 使用 OpenClawNotifier 发送通知
notifier = OpenClawNotifier(
    channel="telegram",
    target="telegram:5747692163",
    account="8606699467",
    platform_name="小红书"
)
notifier.notify_start("文章标题")
```
