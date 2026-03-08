"""
登录管理模块

提供统一的登录流程管理基类，支持多平台登录状态保存。
"""

from .base_login import BaseLoginManager

__all__ = ['BaseLoginManager']
