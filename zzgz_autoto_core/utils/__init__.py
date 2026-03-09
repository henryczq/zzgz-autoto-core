"""通用工具函数模块 - 消除代码重复"""

import io
import os
import sys
from pathlib import Path


def configure_stdio_utf8():
    """强制 stdout/stderr 使用 UTF-8，避免 Windows 控制台因 Emoji 报错。"""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        elif getattr(sys.stdout, "buffer", None):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        elif getattr(sys.stderr, "buffer", None):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


_LOG_LEVELS = {
    "debug": 10,
    "info": 20,
    "warn": 30,
    "warning": 30,
    "error": 40,
}
_current_log_level = "debug"


def set_log_level(level: str | None) -> str:
    global _current_log_level
    if not level:
        _current_log_level = "info"
        return _current_log_level
    normalized = str(level).strip().lower()
    if normalized not in _LOG_LEVELS:
        normalized = "info"
    _current_log_level = "warn" if normalized == "warning" else normalized
    os.environ["AUTOTO_LOG_LEVEL"] = _current_log_level
    return _current_log_level


def get_log_level() -> str:
    return _current_log_level


def _should_log(level: str) -> bool:
    current = _LOG_LEVELS.get(_current_log_level, 20)
    target = _LOG_LEVELS.get(level, 20)
    return target >= current


def log(level: str, message: str):
    if _should_log(level):
        print(message)


def configure_logging(log_level: str | None = None, verbose: bool = False) -> str:
    if verbose:
        return set_log_level("debug")
    env_level = os.getenv("AUTOTO_LOG_LEVEL")
    return set_log_level(log_level or env_level or "info")


def process_image_paths(image_list: list[str]) -> list[str]:
    """
    过滤不存在的图片并转换为绝对路径

    Args:
        image_list: 图片路径列表

    Returns:
        过滤后存在的图片绝对路径列表
    """
    final_images = []
    for p in image_list:
        path_obj = Path(p)
        if path_obj.exists():
            final_images.append(str(path_obj.resolve()))
    return final_images


def resolve_cover_image(cover_image: str | None) -> str | None:
    """
    处理封面图片路径

    Args:
        cover_image: 封面图片路径

    Returns:
        绝对路径或 None（如果不存在）
    """
    if not cover_image:
        return None
    cover_path = Path(cover_image)
    if cover_path.exists():
        return str(cover_path.resolve())
    return None


def get_skill_dir() -> Path:
    """获取 skill 根目录"""
    # 从 __file__ 向上三级到达项目根目录 (utils -> scripts -> skill_root)
    return Path(__file__).parent.parent.parent.resolve()


def get_data_dir() -> Path:
    """获取数据目录 - 始终返回绝对路径"""
    return get_skill_dir() / "data"


def get_auth_state_path(platform: str = "xhs") -> Path:
    """
    获取登录态文件路径

    Args:
        platform: 平台标识 (xhs, wechat)

    Returns:
        登录态文件路径
    """
    filename = f"auth_state_{platform}.json"
    return get_data_dir() / filename


def get_user_data_dir(platform: str = "xhs") -> Path:
    """
    获取浏览器用户数据目录

    Args:
        platform: 平台标识 (xhs, wechat)

    Returns:
        用户数据目录路径
    """
    suffix = f"_{platform}" if platform != "xhs" else ""
    return get_skill_dir() / "scripts" / f".browser_data{suffix}"


# 导出 OpenClaw 消息相关类
try:
    from .openclaw_messaging import OpenClawMessenger, OpenClawNotifier
    __all__ = ['OpenClawMessenger', 'OpenClawNotifier']
except ImportError:
    __all__ = []

# 导出路径管理器
try:
    from .path_manager import PathManager, get_wechat_paths, get_xhs_paths, get_xhs_search_paths
    __all__.extend(['PathManager', 'get_wechat_paths', 'get_xhs_paths', 'get_xhs_search_paths'])
except ImportError:
    pass


