#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 消息发送工具 - 公共模块
支持多种渠道（飞书、微信、WebChat、Telegram等）
用于 skills 向用户发送消息/图片

依赖：需要 OpenClaw CLI (openclaw) 在 PATH 中
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from utils import log

class OpenClawMessenger:
    """
    OpenClaw 消息发送器
    
    使用 OpenClaw CLI 发送消息到各种渠道
    
    示例:
        # 方式 1: 直接传入参数
        messenger = OpenClawMessenger(
            channel="feishu",
            user_id="ou_xxxxxx"
        )
        messenger.send_text("Hello!")
        messenger.send_image("/path/to/qr.png", "请扫码")
        
        # 方式 2: 从环境变量自动读取
        messenger = OpenClawMessenger.from_env()
        messenger.send_text("自动读取配置")
    """
    
    # 支持的消息渠道
    SUPPORTED_CHANNELS = ["feishu", "wechat", "telegram", "discord", "webchat", "slack"]
    
    def __init__(self, 
                 channel: Optional[str] = None,
                 user_id: Optional[str] = None,
                 session_key: Optional[str] = None):
        """
        初始化消息发送器
        
        Args:
            channel: 消息渠道 (feishu/wechat/telegram等)
            user_id: 用户ID (如飞书的 ou_xxxxxx)
            session_key: 可选的会话密钥
        """
        log("debug", f"[OpenClawMessenger] 初始化开始...")
        log("debug", f"[OpenClawMessenger] 传入参数: channel={channel}, user_id={user_id}, session_key={session_key}")
        self.channel = channel
        self.user_id = user_id
        self.session_key = session_key
        log("debug", f"[OpenClawMessenger] 初始化完成: channel={self.channel}, user_id={self.user_id}")
        
    @classmethod
    def from_env(cls, prefix: str = "OPENCLAW") -> "OpenClawMessenger":
        """
        从环境变量创建实例
        
        读取以下环境变量:
        - {prefix}_CHANNEL (默认: feishu)
        - {prefix}_USER_ID (必需)
        - {prefix}_SESSION_KEY (可选)
        
        Args:
            prefix: 环境变量前缀，默认 "OPENCLAW"
        
        Returns:
            OpenClawMessenger 实例
        
        Raises:
            ValueError: 如果缺少必需的 USER_ID
        
        示例:
            # 设置环境变量
            export OPENCLAW_CHANNEL=feishu
            export OPENCLAW_USER_ID=ou_xxxxxx
            
            # 代码中使用
            messenger = OpenClawMessenger.from_env()
        """
        channel = os.getenv(f"{prefix}_CHANNEL", "feishu")
        user_id = os.getenv(f"{prefix}_USER_ID")
        session_key = os.getenv(f"{prefix}_SESSION_KEY")
        
        if not user_id:
            raise ValueError(
                f"缺少必需的环境变量: {prefix}_USER_ID\n"
                f"请设置: export {prefix}_USER_ID=your_user_id"
            )
        
        return cls(
            channel=channel,
            user_id=user_id,
            session_key=session_key
        )
    
    def is_ready(self) -> bool:
        """检查是否可以发送消息（需要 channel 和 user_id）"""
        ready = self.channel is not None and self.user_id is not None
        log("debug", f"[OpenClawMessenger] is_ready检查: channel={self.channel}, user_id={self.user_id}, ready={ready}")
        return ready
    
    def _build_cmd(self, text: str, image_path: Optional[str] = None) -> str:
        """构建 OpenClaw CLI 命令（返回字符串形式，兼容 Windows 和 Linux）"""
        log("debug", f"[OpenClawMessenger] _build_cmd开始: text={text[:30]}..., image_path={image_path}")
        
        # 检测操作系统
        import platform
        is_windows = platform.system() == "Windows"
        
        # 处理文本：
        # 1. 把物理换行符替换为字面量的 \n 字符（让 CMD 看到的是 \n 文本）
        # 2. 转义双引号防止命令截断
        safe_text = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        # 构建命令
        if is_windows:
            # Windows: 使用 CMD 直接传递
            cmd = f'openclaw message send --channel {self.channel} -t {self.user_id} -m "{safe_text}"'
            if image_path and Path(image_path).exists():
                resolved_path = str(Path(image_path).resolve())
                cmd += f' --media "{resolved_path}"'
        else:
            # Linux/macOS
            cmd = f'openclaw message send --channel {self.channel} -t {self.user_id} -m "{safe_text}"'
            if image_path and Path(image_path).exists():
                resolved_path = str(Path(image_path).resolve())
                cmd += f' --media "{resolved_path}"'
        
        # 将命令写入文件以便调试
        debug_file = Path("last_openclaw_cmd.txt")
        debug_file.write_text(cmd, encoding='utf-8')
        
        log("debug", f"[OpenClawMessenger] 完整命令已保存到: {debug_file.absolute()}")
        log("debug", f"[OpenClawMessenger] 命令长度: {len(cmd)}")
        log("debug", f"[OpenClawMessenger] 命令预览: {cmd[:200]}...")
        return cmd
    
    def send_text(self, text: str, timeout: int = 30) -> bool:
        """
        发送纯文本消息
        
        Args:
            text: 消息文本
            timeout: 超时时间（秒）
        
        Returns:
            是否发送成功
        
        示例:
            messenger.send_text("Hello from OpenClaw!")
        """
        log("debug", f"[OpenClawMessenger] send_text开始: text={text[:50]}...")
        if not self.is_ready():
            log("error", f"❌ 消息发送器未就绪: channel={self.channel}, user_id={self.user_id}")
            return False
        
        cmd = self._build_cmd(text)
        log("debug", f"[OpenClawMessenger] 调用_send发送文本...")
        return self._send(cmd, timeout)
    
    def send_image(self, image_path: str, caption: str = "", timeout: int = 30) -> bool:
        """
        发送图片（可选带文字说明）
        
        Args:
            image_path: 图片文件路径
            caption: 图片说明文字（可选）
            timeout: 超时时间（秒）
        
        Returns:
            是否发送成功
        
        示例:
            messenger.send_image("/path/to/qr.png", "请扫码登录")
        """
        log("debug", f"[OpenClawMessenger] send_image开始: image_path={image_path}, caption={caption[:30]}...")
        if not self.is_ready():
            log("error", f"❌ 消息发送器未就绪: channel={self.channel}, user_id={self.user_id}")
            return False
        
        if not Path(image_path).exists():
            log("error", f"❌ 图片文件不存在: {image_path}")
            return False
        
        text = caption if caption else "图片"
        log("debug", f"[OpenClawMessenger] 调用_build_cmd构建命令...")
        cmd = self._build_cmd(text, image_path)
        log("debug", f"[OpenClawMessenger] 调用_send发送图片...")
        return self._send(cmd, timeout)
    
    def _send(self, cmd: str, timeout: int) -> bool:
        """执行发送命令"""
        log("debug", f"[OpenClawMessenger] _send开始执行...")
        log("debug", f"[OpenClawMessenger] 命令: {cmd}")
        log("debug", f"[OpenClawMessenger] 超时设置: {timeout}秒")
        try:
            log("debug", f"[OpenClawMessenger] 调用subprocess.run...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore',
                shell=True  # openclaw 是 PowerShell 脚本，需要 shell=True
            )
            log("debug", f"[OpenClawMessenger] subprocess执行完成")
            log("debug", f"[OpenClawMessenger] returncode: {result.returncode}")
            log("debug", f"[OpenClawMessenger] stdout: {result.stdout[:200] if result.stdout else 'None'}")
            log("debug", f"[OpenClawMessenger] stderr: {result.stderr[:200] if result.stderr else 'None'}")
            
            if result.returncode == 0:
                log("info", f"✅ 消息发送成功 ({self.channel})")
                return True
            else:
                log("error", f"❌ 发送失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            log("error", "❌ 发送超时")
            return False
        except Exception as e:
            log("error", f"❌ 发送出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def send_image_safe(self, image_path: str, caption: str = "", timeout: int = 30) -> tuple[bool, str]:
        """
        安全发送图片（带完整错误处理和日志）
        
        Args:
            image_path: 图片文件路径
            caption: 图片说明文字
            timeout: 超时时间（秒）
        
        Returns:
            tuple: (是否成功, 状态消息)
        
        示例:
            success, msg = messenger.send_image_safe("/path/to/qr.png", "请扫码")
            if success:
                print(f"✅ {msg}")
            else:
                print(f"❌ {msg}")
        """
        # 检查发送器是否就绪
        if not self.is_ready():
            return False, f"消息发送器未就绪: channel={self.channel}, user_id={self.user_id}"
        
        # 检查图片文件
        if not Path(image_path).exists():
            return False, f"图片文件不存在: {image_path}"
        
        # 尝试发送
        try:
            success = self.send_image(image_path, caption, timeout)
            if success:
                return True, f"二维码已发送到 {self.channel}"
            else:
                return False, "发送失败（可能是openclaw命令执行失败）"
        except Exception as e:
            return False, f"发送时出错: {e}"
    
    def send_text_safe(self, text: str, timeout: int = 30) -> tuple[bool, str]:
        """
        安全发送文本（带完整错误处理和日志）
        
        Args:
            text: 消息文本
            timeout: 超时时间（秒）
        
        Returns:
            tuple: (是否成功, 状态消息)
        """
        # 检查发送器是否就绪
        if not self.is_ready():
            return False, f"消息发送器未就绪: channel={self.channel}, user_id={self.user_id}"
        
        # 尝试发送
        try:
            success = self.send_text(text, timeout)
            if success:
                return True, f"消息已发送到 {self.channel}"
            else:
                return False, "发送失败（可能是openclaw命令执行失败）"
        except Exception as e:
            return False, f"发送时出错: {e}"


class OpenClawNotifier:
    def __init__(
        self,
        channel: Optional[str] = None,
        user_id: Optional[str] = None,
        session_key: Optional[str] = None,
        platform_name: Optional[str] = None,
    ):
        self.platform_name = platform_name or ""
        self.messenger = OpenClawMessenger(channel=channel, user_id=user_id, session_key=session_key)

    def is_ready(self) -> bool:
        return self.messenger.is_ready()

    def notify_text(self, text: str) -> tuple[bool, str]:
        return self.messenger.send_text_safe(text)

    def notify_start(self, title: str) -> tuple[bool, str]:
        message = f"🚀 {self.platform_name}发布服务已启动，请稍等...\n📌 标题: {title[:50]}{'...' if len(title) > 50 else ''}"
        return self.messenger.send_text_safe(message)

    def notify_waiting_review(self, title: str, content_len: int, image_count: int) -> tuple[bool, str]:
        message = (
            f"✅ {self.platform_name}发布成功！\n\n"
            f"⏳ 正在等待审核通过...\n"
            f"📌 标题: {title[:50]}{'...' if len(title) > 50 else ''}\n"
            f"📝 内容: {content_len} 字\n"
            f"🖼️ 图片: {image_count} 张"
        )
        return self.messenger.send_text_safe(message)

    def notify_review_complete(self, title: str, note_url: str) -> tuple[bool, str]:
        message = f"✅ 审核通过！\n\n📌 标题: {title[:50]}{'...' if len(title) > 50 else ''}\n🔗 {note_url}"
        return self.messenger.send_text_safe(message)

    def notify_failure(self, title: str, reason: str) -> tuple[bool, str]:
        message = (
            f"❌ {self.platform_name}发布失败！\n\n"
            f"📌 标题: {title[:50]}{'...' if len(title) > 50 else ''}\n"
            f"❗ 错误: {reason[:100]}{'...' if len(reason) > 100 else ''}"
        )
        return self.messenger.send_text_safe(message)

    def notify_login_required(self, title: str, login_command: str) -> tuple[bool, str]:
        message = (
            f"⚠️ {self.platform_name}发布失败！\n\n"
            f"📌 标题: {title[:50]}{'...' if len(title) > 50 else ''}\n"
            f"❗ 原因: 未登录或登录已过期\n\n"
            f"💡 请运行登录脚本重新登录:\n{login_command}"
        )
        return self.messenger.send_text_safe(message)


def send_notification(text: str, 
                       image_path: Optional[str] = None,
                       channel: Optional[str] = None,
                       user_id: Optional[str] = None) -> bool:
    """
    快速发送通知（便捷函数）
    
    自动从环境变量读取配置，或使用传入的参数
    
    Args:
        text: 消息文本
        image_path: 可选，图片路径
        channel: 可选，覆盖环境变量的渠道
        user_id: 可选，覆盖环境变量的用户ID
    
    Returns:
        是否发送成功
    
    示例:
        # 方式 1: 纯文本
        send_notification("登录成功！")
        
        # 方式 2: 带图片
        send_notification("请扫码", "/path/to/qr.png")
        
        # 方式 3: 覆盖默认配置
        send_notification("Hello", channel="telegram", user_id="123456")
    """
    try:
        # 优先使用传入的参数，否则从环境变量读取
        final_channel = channel or os.getenv("OPENCLAW_CHANNEL", "feishu")
        final_user_id = user_id or os.getenv("OPENCLAW_USER_ID")
        
        if not final_user_id:
            log("error", "❌ send_notification: 未提供 user_id，且未设置 OPENCLAW_USER_ID 环境变量")
            return False
        
        messenger = OpenClawMessenger(
            channel=final_channel,
            user_id=final_user_id
        )
        
        if image_path:
            return messenger.send_image(image_path, text)
        else:
            return messenger.send_text(text)
            
    except Exception as e:
        log("error", f"❌ send_notification 出错: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    log("info", "Testing OpenClawMessenger...")
    
    # 测试 1: 从环境变量创建
    try:
        messenger = OpenClawMessenger.from_env()
        log("info", f"✅ From env: channel={messenger.channel}, user_id={messenger.user_id}")
    except ValueError as e:
        log("warn", f"⚠️  From env failed: {e}")
    
    # 测试 2: 直接传入参数
    messenger2 = OpenClawMessenger(
        channel="feishu",
        user_id="ou_test123"
    )
    log("info", f"✅ Direct: channel={messenger2.channel}, user_id={messenger2.user_id}")
    log("info", f"✅ is_ready: {messenger2.is_ready()}")
