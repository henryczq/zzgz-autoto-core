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
            target="ou_xxxxxx",
            account="8606699467"  # 可选
        )
        messenger.send_text("Hello!")
        messenger.send_image("/path/to/qr.png", "请扫码")
        
        # 方式 2: 从环境变量自动读取
        messenger = OpenClawMessenger.from_env()
        messenger.send_text("自动读取配置")
        
        # 方式 3: 从 Inbound Context (trusted metadata) 读取
        inbound_meta = {
            "channel": "telegram",
            "chat_id": "telegram:5747692163",
            "account_id": "8606699467"
        }
        messenger = OpenClawMessenger.from_inbound_meta(inbound_meta)
    """
    
    # 支持的消息渠道
    SUPPORTED_CHANNELS = ["feishu", "wechat", "telegram", "discord", "webchat", "slack"]
    
    def __init__(self, 
                 channel: Optional[str] = None,
                 target: Optional[str] = None,
                 account: Optional[str] = None,
                 session_key: Optional[str] = None):
        """
        初始化消息发送器
        
        Args:
            channel: 消息渠道 (feishu/wechat/telegram等)
            target: 目标用户ID (如飞书的 ou_xxxxxx, telegram:5747692163)
            account: 可选的账号ID (如 8606699467)
            session_key: 可选的会话密钥
        """
        log("debug", f"[OpenClawMessenger] 初始化开始...")
        log("debug", f"[OpenClawMessenger] 传入参数: channel={channel}, target={target}, account={account}, session_key={session_key}")
        self.channel = channel
        self.target = target
        self.account = account
        self.session_key = session_key
        log("debug", f"[OpenClawMessenger] 初始化完成: channel={self.channel}, target={self.target}, account={self.account}")
        
    @classmethod
    def from_env(cls, prefix: str = "OPENCLAW") -> "OpenClawMessenger":
        """
        从环境变量创建实例
        
        读取以下环境变量:
        - {prefix}_CHANNEL (默认: feishu)
        - {prefix}_TARGET (必需)
        - {prefix}_ACCOUNT (可选)
        - {prefix}_SESSION_KEY (可选)
        
        Args:
            prefix: 环境变量前缀，默认 "OPENCLAW"
        
        Returns:
            OpenClawMessenger 实例
        
        Raises:
            ValueError: 如果缺少必需的 TARGET
        
        示例:
            # 设置环境变量
            export OPENCLAW_CHANNEL=feishu
            export OPENCLAW_TARGET=ou_xxxxxx
            export OPENCLAW_ACCOUNT=8606699467
            
            # 代码中使用
            messenger = OpenClawMessenger.from_env()
        """
        channel = os.getenv(f"{prefix}_CHANNEL", "feishu")
        target = os.getenv(f"{prefix}_TARGET")
        account = os.getenv(f"{prefix}_ACCOUNT")
        session_key = os.getenv(f"{prefix}_SESSION_KEY")
        
        if not target:
            raise ValueError(
                f"缺少必需的环境变量: {prefix}_TARGET\n"
                f"请设置: export {prefix}_TARGET=your_target_id"
            )
        
        return cls(
            channel=channel,
            target=target,
            account=account,
            session_key=session_key
        )
    
    @classmethod
    def from_inbound_meta(cls, inbound_meta: Dict[str, Any]) -> "OpenClawMessenger":
        """
        从 OpenClaw Inbound Context (trusted metadata) 创建实例
        
        Inbound Meta JSON 格式:
        {
            "schema": "openclaw.inbound_meta.v1",
            "chat_id": "telegram:5747692163",      # -> target
            "account_id": "8606699467",              # -> account (可选)
            "channel": "telegram",                   # -> channel
            "provider": "telegram",
            "surface": "telegram",
            "chat_type": "direct"
        }
        
        Args:
            inbound_meta: OpenClaw 传入的 trusted metadata dict
        
        Returns:
            OpenClawMessenger 实例
        
        Raises:
            ValueError: 如果缺少必需的字段
        
        示例:
            inbound_meta = {
                "channel": "telegram",
                "chat_id": "telegram:5747692163",
                "account_id": "8606699467"
            }
            messenger = OpenClawMessenger.from_inbound_meta(inbound_meta)
        """
        # 从 inbound_meta 提取字段
        channel = inbound_meta.get("channel")
        target = inbound_meta.get("chat_id")  # chat_id 对应 target
        account = inbound_meta.get("account_id")  # account_id 是可选的
        
        if not channel:
            raise ValueError("inbound_meta 缺少必需的字段: channel")
        if not target:
            raise ValueError("inbound_meta 缺少必需的字段: chat_id (映射为 target)")
        
        log("debug", f"[OpenClawMessenger] 从 inbound_meta 创建: channel={channel}, target={target}, account={account}")
        
        return cls(
            channel=channel,
            target=target,
            account=account
        )
        
    def is_ready(self) -> bool:
        """检查是否可以发送消息（需要 channel 和 target）"""
        ready = self.channel is not None and self.target is not None
        log("debug", f"[OpenClawMessenger] is_ready检查: channel={self.channel}, target={self.target}, ready={ready}")
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
        
        # 构建命令 - 使用新的参数名
        cmd_parts = [
            "openclaw",
            "message",
            "send",
            f"--channel {self.channel}",
            f"--target {self.target}",
            f'-m "{safe_text}"'
        ]
        
        # 添加可选的 account 参数
        if self.account:
            cmd_parts.append(f"--account {self.account}")
        
        # 添加图片
        if image_path and Path(image_path).exists():
            resolved_path = str(Path(image_path).resolve())
            cmd_parts.append(f'--media "{resolved_path}"')
        
        cmd = " ".join(cmd_parts)
        
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
            log("error", f"❌ 消息发送器未就绪: channel={self.channel}, target={self.target}")
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
            log("error", f"❌ 消息发送器未就绪: channel={self.channel}, target={self.target}")
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
            return False, f"消息发送器未就绪: channel={self.channel}, target={self.target}"
        
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
            return False, f"消息发送器未就绪: channel={self.channel}, target={self.target}"
        
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
        target: Optional[str] = None,
        account: Optional[str] = None,
        session_key: Optional[str] = None,
        platform_name: Optional[str] = None,
    ):
        self.platform_name = platform_name or ""
        self.messenger = OpenClawMessenger(channel=channel, target=target, account=account, session_key=session_key)

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
                       target: Optional[str] = None,
                       account: Optional[str] = None) -> bool:
    """
    快速发送通知（便捷函数）
    
    自动从环境变量读取配置，或使用传入的参数
    
    Args:
        text: 消息文本
        image_path: 可选，图片路径
        channel: 可选，覆盖环境变量的渠道
        target: 可选，覆盖环境变量的目标用户ID
        account: 可选，覆盖环境变量的账号ID
    
    Returns:
        是否发送成功
    
    示例:
        # 方式 1: 纯文本
        send_notification("登录成功！")
        
        # 方式 2: 带图片
        send_notification("请扫码", "/path/to/qr.png")
        
        # 方式 3: 覆盖默认配置
        send_notification("Hello", channel="telegram", target="123456", account="8606699467")
    """
    try:
        # 优先使用传入的参数，否则从环境变量读取
        final_channel = channel or os.getenv("OPENCLAW_CHANNEL", "feishu")
        final_target = target or os.getenv("OPENCLAW_TARGET")
        final_account = account or os.getenv("OPENCLAW_ACCOUNT")
        
        if not final_target:
            log("error", "❌ send_notification: 未提供 target，且未设置 OPENCLAW_TARGET 环境变量")
            return False
        
        messenger = OpenClawMessenger(
            channel=final_channel,
            target=final_target,
            account=final_account
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
        log("info", f"✅ From env: channel={messenger.channel}, target={messenger.target}, account={messenger.account}")
    except ValueError as e:
        log("warn", f"⚠️  From env failed: {e}")
    
    # 测试 2: 直接传入参数
    messenger2 = OpenClawMessenger(
        channel="feishu",
        target="ou_test123",
        account="8606699467"
    )
    log("info", f"✅ Direct: channel={messenger2.channel}, target={messenger2.target}, account={messenger2.account}")
    log("info", f"✅ is_ready: {messenger2.is_ready()}")
    
    # 测试 3: 从 inbound_meta 创建
    try:
        inbound_meta = {
            "schema": "openclaw.inbound_meta.v1",
            "chat_id": "telegram:5747692163",
            "account_id": "8606699467",
            "channel": "telegram",
            "provider": "telegram",
            "surface": "telegram",
            "chat_type": "direct"
        }
        messenger3 = OpenClawMessenger.from_inbound_meta(inbound_meta)
        log("info", f"✅ From inbound_meta: channel={messenger3.channel}, target={messenger3.target}, account={messenger3.account}")
    except ValueError as e:
        log("warn", f"⚠️  From inbound_meta failed: {e}")
