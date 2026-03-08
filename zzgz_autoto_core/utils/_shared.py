from pathlib import Path

from playwright.sync_api import sync_playwright, Error as PlaywrightError

from ..core.data import (
    ensure_test_placeholder,
    is_url,
    load_article_payload,
    save_article_payload,
)
from ..core.ui import _fill_richtext, _ui_settle
from ..core.platform_config import get_platform_config
from ..platforms.xhs.flow_publish import publish_to_xhs
from ..sources.web_scraper import scrape_web_article
from . import (
    get_skill_dir,
    get_data_dir,
    get_auth_state_path,
    get_user_data_dir,
    process_image_paths,
    resolve_cover_image,
    configure_stdio_utf8,
    configure_logging,
    log,
    get_log_level,
    set_log_level,
)

# 获取当前脚本所在目录 (scripts 目录)
SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
# 注意：AUTH_STATE_PATH 现在通过 get_auth_state_path("xhs") 动态获取
# 避免硬编码路径，确保使用正确的 skill 数据目录
AUTH_STATE_PATH = get_auth_state_path("xhs")
USER_DATA_DIR = SCRIPTS_DIR / ".playwright-profile"

__all__ = [
    "sync_playwright",
    "PlaywrightError",
    "publish_to_xhs",
    "scrape_web_article",
    "is_url",
    "ensure_test_placeholder",
    "load_article_payload",
    "save_article_payload",
    "_ui_settle",
    "_fill_richtext",
    "SCRIPTS_DIR",
    "AUTH_STATE_PATH",
    "USER_DATA_DIR",
    # 新增的工具函数
    "get_skill_dir",
    "get_data_dir",
    "get_auth_state_path",
    "get_user_data_dir",
    "process_image_paths",
    "resolve_cover_image",
    "configure_stdio_utf8",
    "configure_logging",
    "log",
    "get_log_level",
    "set_log_level",
    "get_platform_config",
]
