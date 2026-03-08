"""平台配置管理 - 集中管理各平台特性和限制"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class PlatformLimits:
    """平台限制配置"""
    title_max_length: int
    content_max_length: int
    image_max_count: int = 9
    video_max_length: int | None = None


@dataclass
class PlatformFeatures:
    """平台功能特性"""
    supports_api: bool = False
    supports_playwright: bool = True
    supports_draft: bool = True
    supports_immediate_publish: bool = True
    supports_auto_cover: bool = False
    supports_html_content: bool = False
    supports_markdown: bool = False


@dataclass
class PlatformConfig:
    """平台完整配置"""
    name: str
    display_name: str
    limits: PlatformLimits
    features: PlatformFeatures
    # 内容转换器：将原始内容转换为目标平台格式
    content_formatter: Callable[[str], str] | None = None
    # 标题转换器：处理标题长度和格式
    title_formatter: Callable[[str], str] | None = None


# ========== 平台特定的转换器 ==========

def xhs_content_formatter(content: str) -> str:
    """
    小红书内容格式化 - 美化版
    - 限制 1000 字
    - 添加 Emoji 表情
    - 优化分段和可读性
    - 添加话题标签
    """
    import re

    # 清理换行符
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # 移除多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)

    # 分段处理 - 每段不要太长
    paragraphs = content.split('\n\n')
    formatted_paragraphs = []

    # 小红书常用 Emoji
    emojis = ['✨', '💡', '📌', '🔥', '⭐', '💪', '🎯', '📚', '💎', '🌟']

    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue

        # 如果段落太长，按句子分割
        if len(para) > 150:
            sentences = re.split(r'([。！？.!?])', para)
            new_para = ""
            for j in range(0, len(sentences) - 1, 2):
                sentence = sentences[j] + (sentences[j+1] if j+1 < len(sentences) else "")
                new_para += sentence
                # 每3个句子换行
                if (j // 2 + 1) % 3 == 0:
                    new_para += "\n"
            para = new_para.strip()

        # 为重要段落添加 Emoji（每隔2-3段）
        if i % 3 == 0 and i < len(paragraphs) - 1:
            emoji = emojis[i % len(emojis)]
            para = f"{emoji} {para}"

        formatted_paragraphs.append(para)

    # 合并段落
    content = '\n\n'.join(formatted_paragraphs)

    # 自动提取关键词作为话题标签（简单实现）
    # 提取2-4字的名词作为标签候选
    words = re.findall(r'[\u4e00-\u9fa5]{2,4}', content)
    word_freq = {}
    for word in words:
        if len(word) >= 2 and len(word) <= 4:
            word_freq[word] = word_freq.get(word, 0) + 1

    # 选择出现频率较高的词作为标签（最多3个）
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
    tags = [f"#{word}" for word, _ in top_words if word_freq[word] > 1]

    # 如果没有高频词，添加通用标签
    if not tags:
        tags = ['#干货分享', '#经验分享', '#学习笔记']

    # 添加标签到末尾
    content += f"\n\n{' '.join(tags[:3])}"

    # 添加互动引导
    content += "\n\n💬 觉得有用的话记得点赞收藏哦~"

    # 截断到限制长度（预留空间）
    if len(content) > 1000:
        content = content[:997] + "..."

    return content


def xhs_title_formatter(title: str) -> str:
    """
    小红书标题格式化 - 美化版
    - 限制 20 字
    - 去除多余空格
    - 添加吸引人的前缀
    """
    title = str(title).strip()
    
    # 去除多余空格
    title = " ".join(title.split())
    
    # 小红书热门标题前缀
    attractive_prefixes = [
        "🔥", "💡", "✨", "📌", "⭐", "🎯", "💎", "🌟",
        "建议收藏", "干货", "必看", "超实用"
    ]
    
    # 检查是否已有 Emoji 或前缀
    has_prefix = any(title.startswith(p) for p in attractive_prefixes)
    
    # 如果没有前缀且长度允许，添加一个
    if not has_prefix and len(title) <= 17:
        # 根据内容选择合适的前缀
        if any(word in title for word in ["方法", "技巧", "攻略", "教程"]):
            title = f"💡{title}"
        elif any(word in title for word in ["推荐", "分享", "必看", "干货"]):
            title = f"🔥{title}"
        elif any(word in title for word in ["新手", "入门", "基础"]):
            title = f"📌{title}"
        else:
            title = f"✨{title}"
    
    return title[:20]


def wechat_content_formatter(content: str) -> str:
    """
    微信公众号内容格式化
    - 支持较长内容
    - 转换为 HTML 格式
    """
    # # 简单处理：将换行转为 <br> 和 <p> 标签
    # paragraphs = content.split("\n\n")
    # html_parts = []
    # for p in paragraphs:
    #     p = p.strip()
    #     if p:
    #         # 处理单行换行
    #         p = p.replace("\n", "<br>")
    #         html_parts.append(f"<p>{p}</p>")

    # return "\n".join(html_parts)

    """
    微信公众号内容格式化（纯文本）
    - 保持原文格式，不转换为 HTML
    """
    return content.strip()


def wechat_title_formatter(title: str) -> str:
    """
    微信公众号标题格式化
    - 限制 64 字
    """
    return str(title).strip()[:64]


# ========== 平台配置实例 ==========

PLATFORM_CONFIGS: dict[str, PlatformConfig] = {
    "xhs": PlatformConfig(
        name="xhs",
        display_name="小红书",
        limits=PlatformLimits(
            title_max_length=20,
            content_max_length=1000,
            image_max_count=9,
        ),
        features=PlatformFeatures(
            supports_api=False,
            supports_playwright=True,
            supports_draft=True,
            supports_immediate_publish=True,
            supports_auto_cover=True,
        ),
        content_formatter=xhs_content_formatter,
        title_formatter=xhs_title_formatter,
    ),
    "wechat": PlatformConfig(
        name="wechat",
        display_name="微信公众号",
        limits=PlatformLimits(
            title_max_length=64,
            content_max_length=20000,  # 公众号实际限制较大
            image_max_count=50,
        ),
        features=PlatformFeatures(
            supports_api=True,  # 支持API发布
            supports_playwright=True,
            supports_draft=True,
            supports_immediate_publish=True,
            supports_auto_cover=True,
            supports_html_content=True,
        ),
        content_formatter=wechat_content_formatter,
        title_formatter=wechat_title_formatter,
    ),
}


def get_platform_config(platform: str) -> PlatformConfig:
    """
    获取平台配置

    Args:
        platform: 平台标识 (xhs, wechat)

    Returns:
        平台配置对象

    Raises:
        ValueError: 未知平台
    """
    if platform not in PLATFORM_CONFIGS:
        raise ValueError(f"未知平台: {platform}。支持的平台: {list(PLATFORM_CONFIGS.keys())}")
    return PLATFORM_CONFIGS[platform]


def list_supported_platforms() -> list[dict]:
    """列出所有支持的平台信息"""
    return [
        {
            "name": config.name,
            "display_name": config.display_name,
            "api_supported": config.features.supports_api,
            "playwright_supported": config.features.supports_playwright,
        }
        for config in PLATFORM_CONFIGS.values()
    ]
