"""
发布器基类
提供统一的内容发布框架
"""

import argparse
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple

from playwright.sync_api import sync_playwright

from ..core.data import load_article_payload
from ..core.platform_config import get_platform_config
from ..utils._shared import process_image_paths
from ..utils import configure_stdio_utf8, configure_logging, get_user_data_dir


class BasePublisher(ABC):
    """
    内容发布器基类
    
    子类需要实现:
    - get_platform_name(): 返回平台名称
    - get_auth_state_path(): 返回登录态文件路径
    - init_browser_context(): 初始化浏览器上下文
    - do_publish(): 执行发布操作
    """
    
    def __init__(self):
        """初始化发布器"""
        configure_stdio_utf8()
        self.platform_config = None
        self.notifier = None
        
    @abstractmethod
    def get_platform_name(self) -> str:
        """返回平台名称标识符（如 'xhs', 'wechat'）"""
        pass
    
    @abstractmethod
    def get_auth_state_path(self) -> Path:
        """返回登录态文件路径"""
        pass
    
    def get_user_data_dir(self) -> Path:
        """获取用户数据目录"""
        return get_user_data_dir(self.get_platform_name())
    
    def init_browser_context(self, p, headless: bool, slowmo: int):
        """
        初始化浏览器上下文
        
        Args:
            p: Playwright 实例
            headless: 是否无头模式
            slowmo: 操作减速毫秒
        
        Returns:
            (context, is_persistent) 元组
        """
        auth_path = self.get_auth_state_path()
        user_data_dir = self.get_user_data_dir()
        browser_args = ["--disable-blink-features=AutomationControlled"]
        
        if auth_path.exists():
            print(f"✅ 发现配置文件: {auth_path}")
            try:
                browser = p.chromium.launch(
                    headless=headless,
                    args=browser_args,
                    slow_mo=max(0, slowmo)
                )
                context = browser.new_context(storage_state=str(auth_path))
                return context, False
            except Exception as e:
                print(f"使用 {auth_path.name} 启动失败: {e}，回退到持久化目录...")
        else:
            print(f"未找到登录配置文件: {auth_path}")
        
        # 使用持久化目录
        print(f"ℹ️ 使用持久化目录: {user_data_dir.name}")
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=headless,
            args=browser_args,
            slow_mo=max(0, slowmo)
        )
        return context, True
    
    def get_notifier(self, channel: str, target: str, account: Optional[str] = None, 
                     session_key: Optional[str] = None):
        """
        获取通知器实例
        
        Args:
            channel: 消息渠道
            target: 目标用户ID
            account: 账号ID（可选）
            session_key: 会话密钥（可选）
        
        Returns:
            OpenClawNotifier 实例或 None
        """
        try:
            from ..utils.openclaw_messaging import OpenClawNotifier
            return OpenClawNotifier(
                channel=channel,
                target=target,
                account=account,
                session_key=session_key,
                platform_name=self.platform_config.display_name if self.platform_config else ""
            )
        except ImportError as e:
            print(f"⚠️ 导入消息发送器失败: {e}")
            return None
    
    def load_article_data(self, data_path: Optional[str] = None, 
                          title: str = "", content: str = "", 
                          images: str = "") -> Tuple[str, str, List[str]]:
        """
        加载文章数据
        
        Args:
            data_path: article.json 路径
            title: 标题
            content: 内容
            images: 图片路径列表（逗号分隔）
        
        Returns:
            (title, content, image_list) 元组
        """
        image_list = []
        
        if data_path:
            payload = load_article_payload(Path(data_path))
            title = title or payload.get("title", "")
            content = content or payload.get("content", "")
            image_list = payload.get("images", [])
        
        if images:
            image_list = [s.strip() for s in images.split(",")]
        
        # 处理图片路径
        final_images = process_image_paths(image_list)
        
        return title, content, final_images
    
    def apply_platform_formatting(self, title: str, content: str) -> Tuple[str, str]:
        """
        应用平台特定的格式化和截断
        
        Args:
            title: 标题
            content: 内容
        
        Returns:
            (formatted_title, formatted_content) 元组
        """
        if not self.platform_config:
            self.platform_config = get_platform_config(self.get_platform_name())
        
        if self.platform_config.title_formatter:
            title = self.platform_config.title_formatter(title)
        if self.platform_config.content_formatter:
            content = self.platform_config.content_formatter(content)
        
        return title, content
    
    def check_login_status(self) -> bool:
        """检查登录状态"""
        return self.get_auth_state_path().exists()
    
    def notify_login_required(self, title: str, target: str, channel: str, account: Optional[str] = None):
        """
        发送登录提醒通知
        
        Args:
            title: 文章标题
            target: 目标用户ID
            channel: 消息渠道
            account: 账号ID（可选）
        
        Returns:
            bool: 是否发送成功
        """
        if not self.notifier or not self.notifier.is_ready():
            return False
        
        login_command = f"python scripts/start_{self.get_platform_name()}_login.py --target {target} --channel {channel}"
        if account:
            login_command += f" --account {account}"
        
        return self.notifier.notify_login_required(title, login_command)
    
    def create_base_argument_parser(self) -> argparse.ArgumentParser:
        """
        创建基础参数解析器
        
        Returns:
            ArgumentParser 实例
        """
        parser = argparse.ArgumentParser(description=f"发布内容到{self.get_platform_name()}")
        
        # 数据参数
        parser.add_argument("--data_path", help="article.json 的路径")
        parser.add_argument("--title", help="标题")
        parser.add_argument("--content", help="正文内容")
        parser.add_argument("--images", help="图片路径列表，逗号分隔")
        
        # 浏览器参数
        parser.add_argument("--headless", action="store_true", help="无头模式运行")
        parser.add_argument("--slowmo", type=int, default=800, help="每步操作减速毫秒")
        parser.add_argument("--login-timeout", type=int, default=120, help="登录等待秒数")
        
        # 日志参数
        parser.add_argument("--log-level", help="日志级别（debug/info/warn/error）")
        parser.add_argument("--verbose", action="store_true", help="等价于 --log-level debug")
        
        # 消息通知参数（从 Inbound Context 获取）
        parser.add_argument('--channel',
                           default=os.getenv('OPENCLAW_CHANNEL', 'feishu'),
                           help='消息渠道（从 Inbound Context 的 channel 获取）')
        parser.add_argument('--target',
                           default=os.getenv('OPENCLAW_TARGET'),
                           help='目标用户ID（从 Inbound Context 的 chat_id 获取）')
        parser.add_argument('--account',
                           default=os.getenv('OPENCLAW_ACCOUNT'),
                           help='账号ID（从 Inbound Context 的 account_id 获取，可选）')
        parser.add_argument('--session-key',
                           default=os.getenv('OPENCLAW_SESSION_KEY'),
                           help='会话密钥（可选）')
        
        return parser
    
    def print_publish_info(self, title: str, content: str, images: List[str], **extra_info):
        """
        打印发布信息
        
        Args:
            title: 标题
            content: 内容
            images: 图片列表
            **extra_info: 额外的信息（如封面、作者等）
        """
        print(f"准备发布：")
        print(f"  标题: {title[:30]}{'...' if len(title) > 30 else ''}")
        print(f"  内容长度: {len(content)} 字")
        print(f"  图片数: {len(images)}")
        
        for key, value in extra_info.items():
            if value:
                print(f"  {key}: {value}")
    
    @abstractmethod
    def do_publish(self, context, title: str, content: str, images: List[str], 
                   **kwargs) -> Tuple[bool, Optional[object], str]:
        """
        执行发布操作（子类必须实现）
        
        Args:
            context: Playwright 浏览器上下文
            title: 标题
            content: 内容
            images: 图片列表
            **kwargs: 额外参数
        
        Returns:
            (success, page, error_msg) 元组
        """
        pass
    
    def run(self, args: Optional[argparse.Namespace] = None):
        """
        运行发布流程
        
        Args:
            args: 命令行参数，如果为 None 则自动解析
        
        Returns:
            int: 退出码（0 表示成功）
        """
        if args is None:
            parser = self.create_base_argument_parser()
            args = parser.parse_args()
        
        configure_logging(args.log_level, args.verbose)
        
        # 加载平台配置
        self.platform_config = get_platform_config(self.get_platform_name())
        print(f"📱 目标平台: {self.platform_config.display_name}")
        
        # 加载文章数据
        title, content, images = self.load_article_data(
            args.data_path, args.title, args.content, args.images
        )
        
        # 应用平台格式化
        title, content = self.apply_platform_formatting(title, content)
        
        # 初始化通知器
        if args.target:
            print(f"📱 通知渠道: {args.channel}")
            print(f"👤 目标用户: {args.target}")
            if args.account:
                print(f"👤 账号ID: {args.account}")
            
            self.notifier = self.get_notifier(
                args.channel, args.target, args.account, args.session_key
            )
            
            if self.notifier and self.notifier.is_ready():
                print("✅ 通知器初始化成功")
                start_notify, msg = self.notifier.notify_start(title)
                if start_notify:
                    print(f"📱 已发送启动通知")
                else:
                    print(f"⚠️ 发送启动通知失败: {msg}")
        
        # 检查登录状态
        is_logged_in = self.check_login_status()
        
        if not is_logged_in:
            if args.target and self.notifier and self.notifier.is_ready():
                print("❌ 未找到登录状态，需要重新登录")
                self.notify_login_required(title, args.target, args.channel, args.account)
                return 1
            else:
                print("⚠️ 未找到登录状态，将等待扫码登录...")
        
        # 执行发布
        success = False
        error_msg = ""
        
        with sync_playwright() as p:
            context, is_persistent = self.init_browser_context(
                p, args.headless, args.slowmo
            )
            
            try:
                success, page, error_msg = self.do_publish(
                    context, title, content, images, args=args
                )
                
                if success:
                    print(f"✅ {self.platform_config.display_name}发布成功！")
                    
                    # 发送成功通知
                    if self.notifier and self.notifier.is_ready():
                        self.notifier.notify_success(title)
                    
                    # 自动导出会话状态
                    if is_persistent:
                        auth_path = self.get_auth_state_path()
                        if not auth_path.exists():
                            auth_path.parent.mkdir(parents=True, exist_ok=True)
                            context.storage_state(path=str(auth_path))
                            print(f"💡 已自动导出会话状态到: {auth_path}")
                else:
                    print(f"❌ 发布失败: {error_msg}")
                    
                    # 发送失败通知
                    if self.notifier and self.notifier.is_ready():
                        self.notifier.notify_failure(title, error_msg)
                    
                    return 1
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ 发布失败: {error_msg}")
                import traceback
                traceback.print_exc()
                
                # 发送失败通知
                if self.notifier and self.notifier.is_ready():
                    self.notifier.notify_failure(title, error_msg)
                
                return 1
            finally:
                context.close()
        
        return 0
