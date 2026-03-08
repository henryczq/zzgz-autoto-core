"""核心模块 - 提供数据处理、图片处理、UI交互和平台配置功能"""

from .data import (
    is_url,
    ensure_test_placeholder,
    load_article_payload,
    save_article_payload,
)
from .image_utils import (
    download_image,
    search_and_download_cover,
    get_default_cover,
)
from .ui import (
    _ui_settle,
    _fill_richtext,
)
from .platform_config import (
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
