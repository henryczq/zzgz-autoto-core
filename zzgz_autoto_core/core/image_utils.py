"""图片工具模块 - 用于下载和处理图片。"""

import os
import tempfile
import urllib.parse
from pathlib import Path

import requests


def download_image(url: str, save_path: str | None = None, timeout: int = 30) -> str:
    """
    从URL下载图片到本地。

    Args:
        url: 图片URL
        save_path: 保存路径（可选，默认使用临时文件）
        timeout: 请求超时秒数

    Returns:
        图片保存的本地路径

    Raises:
        ValueError: URL无效或下载失败
    """
    if not url or not url.startswith(("http://", "https://")):
        raise ValueError(f"无效的图片URL: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": urllib.parse.urlparse(url).netloc,
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        # 确定文件扩展名
        content_type = response.headers.get("Content-Type", "")
        ext = _get_extension_from_content_type(content_type) or _get_extension_from_url(url) or ".jpg"

        # 确定保存路径
        if save_path:
            save_path = Path(save_path)
            if not save_path.suffix:
                save_path = save_path.with_suffix(ext)
        else:
            save_dir = Path(tempfile.gettempdir()) / "wechat_covers"
            save_dir.mkdir(parents=True, exist_ok=True)
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            save_path = save_dir / f"cover_{url_hash}{ext}"

        # 保存图片
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return str(save_path)

    except requests.RequestException as e:
        raise ValueError(f"下载图片失败: {e}")


def search_and_download_cover(keyword: str, save_path: str | None = None) -> str:
    """
    从百度图片搜索并下载封面图片。

    Args:
        keyword: 搜索关键词
        save_path: 保存路径（可选）

    Returns:
        图片保存的本地路径

    Raises:
        ValueError: 搜索或下载失败
    """
    # 百度图片搜索
    search_url = f"https://image.baidu.com/search/index?tn=baiduimage&word={urllib.parse.quote(keyword)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()

        # 从搜索结果页面提取图片URL
        # 百度图片页面包含 "data-imgurl" 属性
        import re
        img_urls = re.findall(r'"hoverURL":"([^"]+)"', response.text)
        img_urls += re.findall(r'"middleURL":"([^"]+)"', response.text)
        img_urls += re.findall(r'"objURL":"([^"]+)"', response.text)

        # 过滤有效的图片URL
        valid_urls = [url.replace("\\/", "/") for url in img_urls if url.startswith("http")]

        if not valid_urls:
            # 如果没有找到，使用默认封面
            return get_default_cover(save_path)

        # 尝试下载第一张可用的图片
        for img_url in valid_urls[:5]:
            try:
                return download_image(img_url, save_path, timeout=20)
            except ValueError:
                continue

        # 如果所有图片都下载失败，使用默认封面
        return get_default_cover(save_path)

    except Exception as e:
        print(f"搜索封面图片失败: {e}，使用默认封面")
        return get_default_cover(save_path)


def get_default_cover(save_path: str | None = None) -> str:
    """
    获取默认封面图片（纯色背景图片）。

    Args:
        save_path: 保存路径（可选）

    Returns:
        图片保存的本地路径
    """
    # 创建一个简单的默认封面图片（使用PIL生成）
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 创建渐变背景
        width, height = 900, 500
        img = Image.new("RGB", (width, height), color=(64, 128, 200))
        draw = ImageDraw.Draw(img)

        # 添加简单装饰
        for i in range(0, width, 50):
            draw.line([(i, 0), (i + 100, height)], fill=(70, 140, 210), width=2)

        # 确定保存路径
        if not save_path:
            save_dir = Path(tempfile.gettempdir()) / "wechat_covers"
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = str(save_dir / "default_cover.png")

        img.save(save_path, "PNG")
        return save_path

    except ImportError:
        # 如果没有PIL，下载一个简单的在线图片
        default_url = "https://picsum.photos/900/500"
        return download_image(default_url, save_path)


def _get_extension_from_content_type(content_type: str) -> str | None:
    """从Content-Type获取文件扩展名。"""
    content_type = content_type.lower().split(";")[0].strip()
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
    }
    return mapping.get(content_type)


def _get_extension_from_url(url: str) -> str | None:
    """从URL获取文件扩展名。"""
    path = urllib.parse.urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
        return ext if ext != ".jpeg" else ".jpg"
    return None
