#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台登录管理器基类
提供统一的登录流程框架，支持二维码捕获、消息发送、登录等待等功能

子类需要实现:
- get_platform_name(): 返回平台名称
- get_capturer_class(): 返回二维码捕获器类
- create_capturer(): 创建并返回二维码捕获器实例
- get_auth_state_path(): 返回登录态文件路径
- get_qr_output_dir(): 返回二维码输出目录
- get_status_dir(): 返回状态文件目录（可选）
"""

import sys
import io
import asyncio
import platform
import argparse
import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Type, Dict, Any

from utils import configure_logging


# 设置无缓冲输出，确保日志实时显示
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)


class BaseLoginManager(ABC):
    """
    登录管理器基类
    
    统一登录流程:
    1. 获取二维码 (capture_qr)
    2. 发送二维码给用户 (send_qr_to_user)
    3. 等待用户扫码登录 (wait_for_login)
    4. 发送结果通知 (send_notification)
    
    子类只需实现平台特定的方法
    """
    
    def __init__(self, 
                 headless: bool = False,
                 channel: Optional[str] = None,
                 user_id: Optional[str] = None,
                 session_key: Optional[str] = None,
                 timeout: int = 120):
        """
        初始化登录管理器
        
        Args:
            headless: 是否使用无头模式
            channel: 消息渠道 (feishu/wechat等)
            user_id: 用户ID
            session_key: 会话密钥
            timeout: 二维码捕获超时时间（秒）
        """
        self.headless = headless
        self.channel = channel
        self.user_id = user_id
        self.session_key = session_key
        self.timeout = timeout
        
        # 自动检测Linux系统启用无头模式
        if platform.system().lower() == 'linux' and not self.headless:
            print("🐧 检测到Linux系统，自动启用无头模式")
            self.headless = True
        
        # 初始化路径
        self.auth_path = self.get_auth_state_path()
        self.qr_output_dir = self.get_qr_output_dir()
        self.status_dir = self.get_status_dir()
        
        # 初始化消息发送器
        self._messenger = None
        
        # 初始化 capturer 缓存（用于复用浏览器实例）
        self._capturer = None
        
        print(f"\n🎯 {self.get_platform_name()}登录状态自动保存程序")
        print(f"运行模式: {'无头模式' if self.headless else '可视化模式'}")
        print("=" * 50)
    
    # ==================== 抽象方法（子类必须实现） ====================
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """返回平台名称，如 '小红书', '微信' """
        pass
    
    @abstractmethod
    def get_capturer_class(self) -> Type:
        """返回二维码捕获器类"""
        pass
    
    @abstractmethod
    def create_capturer(self):
        """创建并返回二维码捕获器实例"""
        pass
    
    @abstractmethod
    def get_auth_state_path(self) -> Path:
        """返回登录态文件保存路径"""
        pass
    
    @abstractmethod
    def get_qr_output_dir(self) -> Path:
        """返回二维码输出目录"""
        pass
    
    def get_status_dir(self) -> Optional[Path]:
        """
        返回状态文件目录（可选）
        默认返回 None，如果平台需要状态文件可以重写此方法
        """
        return None
    
    # ==================== 消息发送相关 ====================
    
    def _get_messenger(self):
        """
        获取或创建消息发送器实例
        延迟初始化，只在需要时创建
        """
        if self._messenger is None and self.user_id:
            try:
                # 尝试从 core 导入
                core_utils = Path(__file__).parent.parent / "utils"
                if str(core_utils) not in sys.path:
                    sys.path.insert(0, str(core_utils))
                from openclaw_messaging import OpenClawMessenger
                self._messenger = OpenClawMessenger(
                    channel=self.channel,
                    user_id=self.user_id,
                    session_key=self.session_key
                )
                print(f"✅ 消息发送器初始化成功 ({self.channel})")
            except ImportError as e:
                print(f"⚠️  消息发送器初始化失败: {e}")
                self._messenger = None
        
        return self._messenger
    
    def send_qr_to_user(self, qr_path: str) -> bool:
        """
        发送二维码给用户
        
        Args:
            qr_path: 二维码图片路径
            
        Returns:
            是否发送成功
        """
        messenger = self._get_messenger()
        if not messenger:
            print(f"⚠️  未找到消息模块，跳过发送二维码")
            return False
        
        success, msg = messenger.send_image_safe(
            image_path=qr_path,
            caption=f"请使用{self.get_platform_name()}APP扫描此二维码完成登录（5分钟内有效）："
        )
        
        if success:
            print(f"✅ {msg}")
        else:
            print(f"⚠️  {msg}")
        
        return success
    
    def get_login_success_message(self) -> str:
        """
        获取登录成功消息内容
        子类可以重写此方法来自定义成功消息
        """
        return f"✅ {self.get_platform_name()}登录成功！"
    
    def send_login_success_notification(self) -> bool:
        """发送登录成功通知"""
        messenger = self._get_messenger()
        if not messenger:
            return False
        
        success, msg = messenger.send_text_safe(self.get_login_success_message())
        return success
    
    def send_login_failure_notification(self, error: str = "") -> bool:
        """发送登录失败通知"""
        messenger = self._get_messenger()
        if not messenger:
            return False
        
        success, msg = messenger.send_text_safe(
            f"❌ {self.get_platform_name()}登录失败，请重试或检查二维码是否过期。{error}"
        )
        return success
    
    # ==================== 主流程 ====================
    
    async def run(self) -> int:
        """
        执行完整的登录流程
        
        Returns:
            退出码 (0=成功, 1=失败)
        """
        try:
            # 步骤 1: 获取二维码
            print(f"\n🚀 步骤 1/3: 获取二维码...")
            qr_result = await self._capture_qr()
            
            if not qr_result["success"]:
                print(f"❌ 获取二维码失败: {qr_result.get('error', '未知错误')}")
                return 1
            
            qr_path = qr_result.get('file_path', '')
            print(f"✅ 二维码已生成: {qr_path}")
            
            # 步骤 2: 发送二维码给用户（可选）
            message_sent = False
            if self.user_id and qr_path:
                print(f"\n🚀 步骤 2/3: 发送二维码给用户 ({self.channel})...")
                print(f"   目标用户: {self.user_id}")
                message_sent = self.send_qr_to_user(qr_path)
            else:
                print(f"\n⏭️  步骤 2/3: 未提供用户ID，跳过自动发送")
                print(f"   二维码已保存，请手动查看: {qr_path}")
            
            # 步骤 3: 等待用户扫码登录
            print(f"\n🚀 步骤 3/3: 等待扫码登录...")
            print(f"⏳ 最长等待时间: 5分钟")
            
            login_result = await self._wait_for_login(qr_path)
            
            # 发送结果通知
            if login_result["success"]:
                print(f"\n🎉 登录成功!")
                print(f"   📁 二维码: {qr_path}")
                print(f"   🔐 认证: {login_result.get('auth_path', self.auth_path)}")
                
                # 发送成功通知
                if self.user_id:
                    self.send_login_success_notification()
                
                return 0
            else:
                error_msg = login_result.get('error', '未知错误')
                print(f"\n❌ 登录失败: {error_msg}")
                
                # 发送失败通知
                if self.user_id:
                    self.send_login_failure_notification(error_msg)
                
                return 1
                
        except Exception as e:
            print(f"\n❌ 程序执行出错: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def _get_capturer(self):
        """
        获取或创建二维码捕获器实例
        复用同一个实例以保持浏览器状态
        """
        if self._capturer is None:
            self._capturer = self.create_capturer()
        return self._capturer
    
    async def _capture_qr(self) -> Dict[str, Any]:
        """
        捕获二维码
        子类可以重写此方法以实现自定义的二维码捕获逻辑
        """
        capturer = self._get_capturer()
        
        # 检查 capturer 是否有 capture_qr_only 方法（小红书模式）
        if hasattr(capturer, 'capture_qr_only'):
            status_dir = str(self.status_dir) if self.status_dir else None
            return await capturer.capture_qr_only(status_dir=status_dir)
        else:
            # 微信模式：直接调用 capture 方法
            # 注意：微信的 capture 是同步方法，需要包装
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, capturer.capture)
    
    async def _wait_for_login(self, qr_path: str) -> Dict[str, Any]:
        """
        等待用户扫码登录
        子类可以重写此方法以实现自定义的登录等待逻辑
        """
        capturer = self._get_capturer()
        
        # 检查 capturer 是否有 wait_for_login 方法（小红书模式）
        if hasattr(capturer, 'wait_for_login'):
            status_dir = str(self.status_dir) if self.status_dir else None
            return await capturer.wait_for_login(
                auth_path=str(self.auth_path),
                status_dir=status_dir,
                max_wait_time=300,
                check_interval=5
            )
        else:
            # 微信模式：需要子类实现或使用默认逻辑
            return await self._default_wait_for_login(capturer, qr_path)
    
    async def _default_wait_for_login(self, capturer, qr_path: str) -> Dict[str, Any]:
        """
        默认的登录等待逻辑（适用于微信等平台）
        使用 Playwright 直接控制浏览器等待登录
        """
        from playwright.async_api import async_playwright
        
        try:
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                # 创建新的浏览器上下文
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080}
                )
                
                # 创建页面
                page = await context.new_page()
                
                # 访问登录页面
                target_url = getattr(capturer, 'target_url', None)
                if not target_url:
                    return {
                        "success": False,
                        "error": " capturer 没有 target_url 属性"
                    }
                
                print(f"🌐 访问登录页面: {target_url}")
                await page.goto(target_url, wait_until="networkidle", timeout=self.timeout * 1000)
                
                # 等待页面加载
                await page.wait_for_timeout(3000)
                
                print("⏳ 等待用户扫码登录...")
                print(f"   二维码路径: {qr_path}")
                print("   请在手机上确认登录...")
                
                # 等待登录成功（通过URL变化判断）
                try:
                    # 微信：等待跳转到 /home
                    # 小红书：等待跳转到创作者中心
                    await page.wait_for_url("**/home**", timeout=300000)
                    print("✅ 检测到登录成功!")
                    
                    # 等待页面完全加载
                    await page.wait_for_timeout(3000)
                    
                    # 保存登录状态
                    print("💾 正在保存登录状态...")
                    await context.storage_state(path=str(self.auth_path))
                    
                    print(f"✅ 登录状态已保存: {self.auth_path}")
                    
                    await browser.close()
                    
                    return {
                        "success": True,
                        "auth_path": str(self.auth_path)
                    }
                    
                except Exception as e:
                    await browser.close()
                    return {
                        "success": False,
                        "error": f"登录超时或失败: {e}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== 命令行参数解析 ====================
    
    @classmethod
    def parse_args(cls):
        """
        解析命令行参数
        子类可以重写此方法以添加自定义参数
        """
        # 使用类名作为描述，避免创建实例
        platform_name = getattr(cls, '_platform_name', cls.__name__.replace('LoginManager', ''))
        parser = argparse.ArgumentParser(description=f'{platform_name}登录状态自动保存程序')
        parser.add_argument('--headless', action='store_true',
                           help='使用无头模式运行（Ubuntu服务器推荐）')
        parser.add_argument('--log-level',
                           help='日志级别（debug/info/warn/error）')
        parser.add_argument('--verbose', action='store_true',
                           help='等价于 --log-level debug')
        
        # 消息发送相关参数
        parser.add_argument('--channel', 
                           default=os.getenv('OPENCLAW_CHANNEL', 'feishu'),
                           help='消息渠道（默认：feishu，或从环境变量 OPENCLAW_CHANNEL 读取）')
        parser.add_argument('--user-id',
                           default=os.getenv('OPENCLAW_USER_ID'),
                           help='用户ID（或从环境变量 OPENCLAW_USER_ID 读取）')
        parser.add_argument('--session-key',
                           default=os.getenv('OPENCLAW_SESSION_KEY'),
                           help='会话密钥（可选，从环境变量 OPENCLAW_SESSION_KEY 读取）')
        
        return parser.parse_args()
    
    @classmethod
    def main(cls):
        """主入口点"""
        args = cls.parse_args()
        configure_logging(args.log_level, args.verbose)
        
        # 创建实例
        instance = cls(
            headless=args.headless,
            channel=args.channel,
            user_id=args.user_id,
            session_key=args.session_key
        )
        
        # 运行
        try:
            exit_code = asyncio.run(instance.run())
            sys.exit(exit_code)
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断操作")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 程序启动失败: {e}")
            sys.exit(1)
