#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录状态管理器基类
提供统一的登录状态检查、验证和管理流程

子类需要实现:
- get_platform_name(): 返回平台名称
- get_auth_file_path(): 返回认证文件路径
- get_platform_url(): 返回平台URL
- check_login_status(page): 检查登录状态的页面逻辑
"""

import asyncio
import json
import argparse
import platform
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from playwright.async_api import async_playwright, Page


class BaseLoginStateManager(ABC):
    """
    登录状态管理器基类
    
    统一流程:
    1. 加载登录状态 (load_login_state)
    2. 应用登录状态到页面 (apply_login_state)
    3. 验证登录状态有效性 (verify_login_status)
    4. 查询并报告登录状态 (query_login_state)
    
    子类只需实现平台特定的方法
    """
    
    def __init__(self, headless: bool = True):
        """
        初始化登录状态管理器
        
        Args:
            headless: 是否使用无头模式
        """
        self.headless = headless
        
        # 自动检测Linux系统启用无头模式
        if platform.system().lower() == 'linux' and not self.headless:
            print("🐧 检测到Linux系统，自动启用无头模式")
            self.headless = True
    
    # ==================== 抽象方法（子类必须实现） ====================
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """返回平台显示名称，如 '小红书', '微信公众号' """
        pass
    
    @abstractmethod
    def get_platform_key(self) -> str:
        """返回平台标识键，如 'xhs', 'wechat' """
        pass
    
    @abstractmethod
    def get_auth_file_path(self) -> Path:
        """返回认证文件路径"""
        pass
    
    @abstractmethod
    def get_platform_url(self) -> str:
        """返回平台URL用于验证登录状态"""
        pass
    
    @abstractmethod
    async def check_login_status(self, page: Page) -> Tuple[bool, str]:
        """
        检查页面登录状态
        
        Args:
            page: Playwright页面对象
            
        Returns:
            Tuple[bool, str]: (是否登录, 状态消息)
        """
        pass
    
    # ==================== 通用方法（子类可重写） ====================
    
    def get_data_dir(self) -> Path:
        """获取数据目录"""
        return self.get_auth_file_path().parent
    
    def load_login_state(self) -> Optional[Dict]:
        """
        从JSON文件加载登录状态
        
        Returns:
            Dict: 认证状态数据，如果文件不存在则返回None
        """
        auth_file = self.get_auth_file_path()
        
        if not auth_file.exists():
            return None
        
        try:
            with open(auth_file, 'r', encoding='utf-8') as f:
                auth_state = json.load(f)
            return auth_state
        except Exception as e:
            print(f"❌ 加载登录状态失败: {e}")
            return None
    
    async def apply_login_state(self, page: Page, auth_state: Dict) -> bool:
        """
        将登录状态应用到页面
        
        Args:
            page: Playwright页面对象
            auth_state: 认证状态数据
            
        Returns:
            bool: 应用是否成功
        """
        try:
            # 应用cookies
            if 'cookies' in auth_state:
                await page.context.add_cookies(auth_state['cookies'])
                print(f"✅ 已应用 {len(auth_state['cookies'])} 个cookies")
            
            # 应用localStorage
            if 'origins' in auth_state:
                for origin_data in auth_state['origins']:
                    origin = origin_data.get('origin', '')
                    if origin and 'localStorage' in origin_data:
                        try:
                            localStorage_items = origin_data['localStorage']
                            script = """(items) => {
                                items.forEach(item => {
                                    localStorage.setItem(item.name, item.value);
                                });
                            }"""
                            await page.evaluate(script, localStorage_items)
                            print(f"✅ 已应用localStorage项到 {origin}")
                        except Exception as e:
                            print(f"⚠️  应用localStorage到 {origin} 失败: {e}")
            
            return True
        except Exception as e:
            print(f"❌ 应用登录状态失败: {e}")
            return False
    
    async def verify_login_status(self, auth_state: Dict) -> Tuple[bool, str]:
        """
        验证登录状态是否仍然有效
        通过实际访问平台页面来检测
        
        Args:
            auth_state: 认证状态数据
            
        Returns:
            Tuple[bool, str]: (是否有效, 状态消息)
        """
        platform_name = self.get_platform_name()
        platform_url = self.get_platform_url()
        
        print(f"🔍 验证 {platform_name} 登录状态有效性...")
        
        try:
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                # 创建上下文并应用登录状态
                context = await browser.new_context()
                page = await context.new_page()
                
                # 应用保存的登录状态
                await self.apply_login_state(page, auth_state)
                
                # 访问平台页面
                print(f"   🌐 访问: {platform_url}")
                await page.goto(platform_url, wait_until="networkidle", timeout=30000)
                
                # 等待页面加载
                await page.wait_for_timeout(3000)
                
                # 检查登录状态（调用子类实现）
                is_logged_in, message = await self.check_login_status(page)
                
                # 关闭浏览器
                await browser.close()
                
                return is_logged_in, message
                
        except Exception as e:
            print(f"   ❌ 验证过程出错: {e}")
            return False, f"验证失败: {str(e)}"
    
    async def query_login_state(self):
        """查询并报告登录状态"""
        platform_name = self.get_platform_name()
        auth_file = self.get_auth_file_path()
        
        print(f"\n🔍 {platform_name}登录状态查询")
        print("=" * 50)
        print(f"\n📋 检查 {platform_name}...")
        print(f"   认证文件: {auth_file}")
        
        # 加载保存的登录状态
        auth_state = self.load_login_state()
        
        if not auth_state:
            print(f"❌ 未找到 {platform_name} 的登录状态")
            print(f"💡 请先运行登录脚本")
            return False
        
        print(f"✅ 找到 {platform_name} 的登录状态!")
        
        # 获取元数据
        metadata = auth_state.get('metadata', {})
        saved_time = metadata.get('saved_at', 'Unknown')
        cookie_count = len(auth_state.get('cookies', []))
        origin_count = len(auth_state.get('origins', []))
        
        if saved_time != 'Unknown':
            print(f"   保存时间: {saved_time}")
        print(f"   Cookies数量: {cookie_count}")
        print(f"   LocalStorage项数: {len(auth_state.get('origins', [{}])[0].get('localStorage', []))}")
        
        # 验证登录状态有效性
        print(f"\n🔍 开始验证登录状态有效性...")
        is_valid, message = await self.verify_login_status(auth_state)
        
        # 输出总结报告
        print("\n" + "=" * 60)
        print("📊 登录状态验证报告")
        print("=" * 60)
        
        if is_valid:
            print(f"✅ {platform_name}: {message}")
            if saved_time != 'Unknown':
                print(f"   保存时间: {saved_time}")
            print(f"\n🎉 登录状态有效，可正常使用!")
            return True
        else:
            print(f"❌ {platform_name}: {message}")
            if saved_time != 'Unknown':
                print(f"   保存时间: {saved_time}")
            print(f"\n💡 建议重新运行登录脚本更新登录状态")
            return False
    
    def clear_login_state(self) -> bool:
        """
        清除登录状态
        
        Returns:
            bool: 清除是否成功
        """
        try:
            auth_file = self.get_auth_file_path()
            
            if auth_file.exists():
                auth_file.unlink()
                print(f"✅ 已清除 {self.get_platform_name()} 的登录状态")
                return True
            else:
                print(f"⚠️  {self.get_platform_name()} 的登录状态文件不存在")
                return True
                
        except Exception as e:
            print(f"❌ 清除登录状态失败: {e}")
            return False
    
    # ==================== 命令行接口 ====================
    
    @classmethod
    def parse_args(cls):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(description=f'{cls.__name__.replace("LoginStateManager", "")}登录状态管理工具')
        parser.add_argument('--headless', action='store_true', default=True,
                           help='使用无头模式运行（默认启用）')
        parser.add_argument('--no-headless', action='store_true',
                           help='禁用无头模式，使用可视化模式')
        parser.add_argument('--clear', action='store_true',
                           help='清除登录状态')
        
        return parser.parse_args()
    
    @classmethod
    async def main(cls):
        """主入口点"""
        args = cls.parse_args()
        
        # 确定运行模式
        headless = args.headless and not args.no_headless
        
        # 创建实例
        instance = cls(headless=headless)
        platform_name = instance.get_platform_name()
        
        if not args.no_headless:
            print(f"🔐 {platform_name}登录状态管理工具")
            print(f"运行模式: 无头模式\n")
        else:
            print(f"🔐 {platform_name}登录状态管理工具")
            print(f"运行模式: 可视化模式\n")
        
        # 处理清除命令
        if args.clear:
            instance.clear_login_state()
            return
        
        # 执行登录状态查询和验证
        await instance.query_login_state()


# ==================== 便捷函数 ====================

async def verify_login_with_manager(manager_class: type, headless: bool = True) -> bool:
    """
    使用指定的管理器类验证登录状态
    
    Args:
        manager_class: BaseLoginStateManager的子类
        headless: 是否使用无头模式
        
    Returns:
        bool: 登录是否有效
    """
    manager = manager_class(headless=headless)
    auth_state = manager.load_login_state()
    
    if not auth_state:
        return False
    
    is_valid, _ = await manager.verify_login_status(auth_state)
    return is_valid
