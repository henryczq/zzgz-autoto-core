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
