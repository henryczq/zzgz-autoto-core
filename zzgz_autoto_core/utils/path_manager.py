#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一路径管理模块

提供跨技能的标准化路径管理，支持：
1. 从环境变量 ZZGZ_DATA_PATH 读取基础路径
2. 默认使用 ~/.openclaw/media 作为基础路径
3. 每个技能有独立的子目录

使用示例:
    from zzgz_autoto_core.utils.path_manager import PathManager
    
    # 初始化路径管理器（技能名称会自动作为子目录）
    paths = PathManager("zzgz-autoto-wechat")
    
    # 获取各种目录
    auth_path = paths.get_auth_state_path()  # 登录态文件路径
    qr_dir = paths.get_qr_dir()              # 二维码目录
    article_dir = paths.get_article_dir()    # 文章目录
    data_dir = paths.get_data_dir()          # 数据目录
"""

import os
from pathlib import Path
from typing import Optional


class PathManager:
    """
    统一路径管理器
    
    管理技能相关的所有文件路径，确保路径在 OpenClaw 允许的范围内
    """
    
    # 环境变量名称
    ENV_DATA_PATH = "ZZGZ_DATA_PATH"
    
    # 默认基础路径（相对于用户主目录）
    DEFAULT_BASE_PATH = ".openclaw/media"
    
    def __init__(self, skill_name: str, base_path: Optional[str] = None):
        """
        初始化路径管理器
        
        Args:
            skill_name: 技能名称，将作为子目录名（如：zzgz-autoto-wechat）
            base_path: 可选，自定义基础路径。如果不提供，将使用环境变量或默认值
        """
        self.skill_name = skill_name
        
        # 确定基础路径
        if base_path:
            self.base_path = Path(base_path).expanduser().resolve()
        elif self.ENV_DATA_PATH in os.environ:
            self.base_path = Path(os.environ[self.ENV_DATA_PATH]).expanduser().resolve()
        else:
            self.base_path = Path.home() / self.DEFAULT_BASE_PATH
        
        # 技能专属目录
        self.skill_path = self.base_path / skill_name
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有必要的目录都存在"""
        self.skill_path.mkdir(parents=True, exist_ok=True)
        self.get_data_dir().mkdir(parents=True, exist_ok=True)
        self.get_qr_dir().mkdir(parents=True, exist_ok=True)
        self.get_article_dir().mkdir(parents=True, exist_ok=True)
        self.get_status_dir().mkdir(parents=True, exist_ok=True)
    
    def get_base_path(self) -> Path:
        """获取基础路径"""
        return self.base_path
    
    def get_skill_path(self) -> Path:
        """获取技能根目录"""
        return self.skill_path
    
    def get_data_dir(self) -> Path:
        """获取数据目录"""
        return self.skill_path / "data"
    
    def get_qr_dir(self) -> Path:
        """获取二维码保存目录"""
        return self.skill_path / "qrcodes"
    
    def get_article_dir(self) -> Path:
        """获取文章保存目录"""
        return self.skill_path / "articles"
    
    def get_status_dir(self) -> Path:
        """获取状态文件目录"""
        return self.skill_path / "status"
    
    def get_auth_state_path(self, filename: str = "auth_state.json") -> Path:
        """
        获取登录态文件路径
        
        Args:
            filename: 登录态文件名，默认为 auth_state.json
        """
        return self.get_data_dir() / filename
    
    def get_qr_path(self, filename: str) -> Path:
        """
        获取二维码文件完整路径
        
        Args:
            filename: 二维码文件名
        """
        return self.get_qr_dir() / filename
    
    def get_article_path(self, article_id: str) -> Path:
        """
        获取特定文章目录
        
        Args:
            article_id: 文章ID或目录名
        """
        return self.get_article_dir() / article_id
    
    def get_status_path(self, filename: str) -> Path:
        """
        获取状态文件路径
        
        Args:
            filename: 状态文件名
        """
        return self.get_status_dir() / filename
    
    def get_browser_data_dir(self, platform: str = "xhs") -> Path:
        """
        获取浏览器用户数据目录
        
        Args:
            platform: 平台标识 (xhs, wechat)
        
        Returns:
            浏览器用户数据目录路径
        """
        suffix = f"_{platform}" if platform != "xhs" else ""
        return self.skill_path / "scripts" / f".browser_data{suffix}"
    
    def __repr__(self) -> str:
        return f"PathManager(skill='{self.skill_name}', base='{self.base_path}')"


# 预定义的常用技能路径管理器
def get_wechat_paths() -> PathManager:
    """获取微信技能路径管理器"""
    return PathManager("zzgz-autoto-wechat")


def get_xhs_paths() -> PathManager:
    """获取小红书技能路径管理器"""
    return PathManager("zzgz-autoto-xhs")


def get_xhs_search_paths() -> PathManager:
    """获取小红书搜索技能路径管理器"""
    return PathManager("zzgz-xhs-search")
