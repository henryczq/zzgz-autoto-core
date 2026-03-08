"""
二维码捕获器基类
提供统一的二维码捕获框架
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
import asyncio

from playwright.async_api import async_playwright, Page, Browser


class BaseQrCapturer(ABC):
    """
    二维码捕获器基类
    
    子类需要实现:
    - get_platform_name(): 返回平台名称
    - get_target_url(): 返回目标URL
    - get_qr_selector(): 返回二维码元素选择器
    - get_logged_in_selector(): 返回已登录状态选择器
    """
    
    def __init__(self, output_dir: str, headless: bool = False, timeout: int = 60):
        """
        初始化
        
        Args:
            output_dir: 二维码保存目录
            headless: 是否无头模式
            timeout: 超时时间（秒）
        """
        self.output_dir = Path(output_dir)
        self.headless = headless
        self.timeout = timeout
        self._playwright = None
        self._browser = None
        self._page = None
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """返回平台名称"""
        pass
    
    @abstractmethod
    def get_target_url(self) -> str:
        """返回目标URL"""
        pass
    
    @abstractmethod
    def get_qr_selector(self) -> str:
        """返回二维码元素选择器"""
        pass
    
    @abstractmethod
    def get_logged_in_selector(self) -> str:
        """返回已登录状态选择器"""
        pass
    
    def setup_directory(self):
        """创建保存目录"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_filename(self) -> str:
        """生成文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = self.get_platform_name()
        return f"{platform}_qr_{timestamp}.png"
    
    async def cleanup(self):
        """清理浏览器资源"""
        try:
            if self._browser:
                await self._browser.close()
                self._browser = None
        except:
            pass
        try:
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except:
            pass
        self._page = None
    
    async def init_browser(self) -> tuple[Browser, Page]:
        """
        初始化浏览器
        
        Returns:
            (browser, page) 元组
        """
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()
        await self._page.set_viewport_size({"width": 1920, "height": 1080})
        return self._browser, self._page
    
    async def capture_qr_only(self, status_dir: str = None) -> dict:
        """
        捕获二维码，保持浏览器打开等待登录
        
        Args:
            status_dir: 状态文件保存目录（可选）
        
        Returns:
            dict: 包含 success, file_path, browser, page 等信息
        """
        try:
            self.setup_directory()
            browser, page = await self.init_browser()
            
            # 访问目标页面
            target_url = self.get_target_url()
            print(f"🌐 访问{self.get_platform_name()}: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
            
            # 等待页面加载
            print("⏳ 等待页面加载...")
            await page.wait_for_timeout(3000)
            
            # 检查是否已登录
            logged_in_selector = self.get_logged_in_selector()
            try:
                user_element = await page.query_selector(logged_in_selector)
                if user_element:
                    print("✅ 已登录，跳过二维码捕获")
                    return {
                        'success': True,
                        'already_logged_in': True,
                        'platform': self.get_platform_name(),
                        'browser': browser,
                        'page': page
                    }
            except:
                pass
            
            # 查找二维码
            print("🔍 查找二维码...")
            qr_selector = self.get_qr_selector()
            qr_element = await page.wait_for_selector(qr_selector, timeout=10000)
            
            if not qr_element:
                print("❌ 未找到二维码")
                await self.cleanup()
                return {'success': False, 'error': '未找到二维码'}
            
            # 截图保存
            filename = self.generate_filename()
            file_path = self.output_dir / filename
            print(f"📸 保存二维码: {file_path}")
            await qr_element.screenshot(path=str(file_path), type="png")
            
            # 如果提供了状态目录，创建状态文件
            if status_dir:
                status_path = Path(status_dir)
                status_path.mkdir(parents=True, exist_ok=True)
                qr_status_file = status_path / "qr_captured.txt"
                qr_status_file.write_text(
                    f"qr_captured_at:{datetime.now().isoformat()}\n"
                    f"qr_path:{file_path.absolute()}\n"
                    f"platform:{self.get_platform_name()}\n",
                    encoding='utf-8'
                )
            
            return {
                'success': True,
                'file_path': str(file_path),
                'filename': filename,
                'platform': self.get_platform_name(),
                'browser': browser,
                'page': page
            }
            
        except Exception as e:
            await self.cleanup()
            return {'success': False, 'error': str(e)}
    
    async def wait_for_login(self, auth_path: str, max_wait_time: int = 300, check_interval: int = 5) -> dict:
        """
        等待用户扫码登录
        
        Args:
            auth_path: 登录态保存路径
            max_wait_time: 最大等待时间（秒）
            check_interval: 检查间隔（秒）
        
        Returns:
            dict: 包含 success, auth_path 等信息
        """
        page = self._page
        browser = self._browser
        
        if not page or not browser:
            return {'success': False, 'error': '浏览器未启动'}
        
        print(f"⏳ 等待用户扫码登录（最多{max_wait_time}秒）...")
        
        logged_in = False
        check_count = 0
        logged_in_selector = self.get_logged_in_selector()
        
        try:
            import time
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                check_count += 1
                elapsed = time.time() - start_time
                
                # 检查是否已登录
                try:
                    user_element = await page.query_selector(logged_in_selector)
                    if user_element:
                        print("✅ 登录成功!")
                        logged_in = True
                        break
                except:
                    pass
                
                # 每10秒输出一次进度
                if check_count % 10 == 0:
                    print(f"   已等待 {int(elapsed)} 秒...")
                
                await asyncio.sleep(check_interval)
                
        except Exception as e:
            print(f"❌ 等待出错: {e}")
        
        if not logged_in:
            print("❌ 登录超时")
            await self.cleanup()
            return {'success': False, 'error': '登录超时'}
        
        # 保存登录态
        print("💾 保存登录状态...")
        auth_path_obj = Path(auth_path)
        auth_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        contexts = browser.contexts
        if contexts:
            await contexts[0].storage_state(path=str(auth_path_obj))
        
        print(f"✅ 已保存到: {auth_path_obj}")
        await self.cleanup()
        
        return {
            'success': True,
            'auth_path': str(auth_path_obj),
            'platform': self.get_platform_name()
        }
