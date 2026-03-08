"""
Zzgz Autoto Core - 多平台自动化核心库

提供内容抓取、数据处理、图片处理等核心功能。
被 zzgz-autoto-xhs 和 zzgz-autoto-wechat 等技能依赖。
"""

__version__ = "1.0.0"

# 导出核心模块接口 - 使用相对导入
from .core.data import (
    is_url,
    ensure_test_placeholder,
    load_article_payload,
    save_article_payload,
)
from .core.image_utils import (
    download_image,
    search_and_download_cover,
    get_default_cover,
)
from .core.ui import (
    _ui_settle,
    _fill_richtext,
)
from .core.platform_config import (
    PlatformLimits,
    PlatformFeatures,
    PlatformConfig,
    get_platform_config,
    list_supported_platforms,
)

__all__ = [
    # 数据模块
    "is_url",
    "ensure_test_placeholder",
    "load_article_payload",
    "save_article_payload",
    # 图片模块
    "download_image",
    "search_and_download_cover",
    "get_default_cover",
    # UI模块
    "_ui_settle",
    "_fill_richtext",
    # 平台配置
    "PlatformLimits",
    "PlatformFeatures",
    "PlatformConfig",
    "get_platform_config",
    "list_supported_platforms",
]
