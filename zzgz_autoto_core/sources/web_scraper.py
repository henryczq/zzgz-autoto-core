"""
通用网页文章抓取模块
支持微信公众号和其他任意网页
使用 Playwright 无头模式，避免反爬
"""

import time
import urllib.request
from pathlib import Path


def is_wechat_url(url: str) -> bool:
    """判断是否为微信公众号文章链接"""
    return "mp.weixin.qq.com" in url


def scrape_web_article(page, url: str, output_root: Path, max_images: int = 3):
    """
    通用网页文章抓取
    
    Args:
        page: Playwright page 对象
        url: 文章链接
        output_root: 输出目录
        max_images: 最大下载图片数
    
    Returns:
        tuple: (title, content, downloaded_images, article_dir)
    """
    print(f"正在抓取文章: {url}")
    
    # 访问页面
    page.goto(url)
    
    # 等待页面加载
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except:
        print("页面加载超时(networkidle)，尝试继续...")
    
    # 根据是否为微信链接选择策略
    if is_wechat_url(url):
        return _scrape_wechat(page, output_root, max_images)
    else:
        return _scrape_generic(page, output_root, max_images)


def _scrape_wechat(page, output_root: Path, max_images: int):
    """抓取微信公众号文章 - 复用 wechat.py 的逻辑"""
    print("使用微信公众号抓取策略")
    
    # 等待页面完全加载
    print("  等待页面加载...")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except:
        print("  networkidle 超时，继续等待 DOM...")
    
    # 额外等待，确保 JavaScript 渲染完成
    page.wait_for_timeout(3000)
    
    # 等待标题加载（增加超时时间）
    try:
        page.wait_for_selector("#activity-name", timeout=20000)
    except Exception as e:
        # 保存截图用于调试
        debug_dir = output_root / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = debug_dir / f"wechat_error_{timestamp}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"  已保存错误截图: {screenshot_path}")
        raise Exception(f"未找到微信文章标题: {e}")
    
    # 获取标题
    title = page.inner_text("#activity-name").strip()
    
    # 获取正文
    content = page.inner_text("#js_content").strip()
    
    # 获取图片 - 微信图片通常在 data-src 中
    img_elements = page.query_selector_all("#js_content img")
    image_urls = []
    for img in img_elements:
        src = img.get_attribute("data-src") or img.get_attribute("src")
        if src and "mmbiz.qpic.cn" in src:
            image_urls.append(src)
        if len(image_urls) >= max_images:
            break
    
    return _save_article(title, content, image_urls, output_root, "wechat")


def _scrape_generic(page, output_root: Path, max_images: int):
    """通用网页抓取（适用于任意网站）"""
    print("使用通用网页抓取策略")
    
    # 尝试多种常见标题选择器
    title_selectors = [
        "h1", "h1.title", "h1.article-title", "h1.post-title",
        ".title", ".article-title", ".post-title",
        "[class*='title']", "[class*='headline']",
        "header h1", "article h1"
    ]
    title = _try_get_text(page, title_selectors, "无标题")
    
    # 尝试多种常见正文选择器
    content_selectors = [
        "article", "main", ".content", ".article-content", ".post-content",
        ".entry-content", ".post-entry", "[class*='content']",
        "[class*='article-body']", "[class*='post-body']",
        "#content", "#main", ".main"
    ]
    content = _try_get_text(page, content_selectors, "")
    
    # 如果没找到内容，尝试获取 body 文本（去掉导航等）
    if not content:
        try:
            content = page.evaluate("""
                () => {
                    const article = document.querySelector('article');
                    if (article) return article.innerText;
                    const main = document.querySelector('main');
                    if (main) return main.innerText;
                    // 获取 body 但排除 nav, header, footer, aside
                    const body = document.body.cloneNode(true);
                    const exclude = body.querySelectorAll('nav, header, footer, aside, script, style, .nav, .header, .footer, .sidebar, .ads');
                    exclude.forEach(el => el.remove());
                    return body.innerText;
                }
            """)
            content = content.strip() if content else ""
        except:
            content = ""
    
    # 获取图片
    img_selectors = [
        "article img", "main img", ".content img", ".article-content img", "img"
    ]
    image_urls = _try_get_images(page, img_selectors, max_images)
    
    return _save_article(title, content, image_urls, output_root, "web")


def _try_get_text(page, selectors, default=""):
    """尝试多个选择器获取文本"""
    for selector in selectors:
        try:
            if page.locator(selector).count() > 0:
                text = page.inner_text(selector).strip()
                if text and len(text) > 10:
                    return text
        except:
            continue
    return default


def _try_get_images(page, selectors, max_images):
    """尝试多个选择器获取图片"""
    image_urls = []
    for selector in selectors:
        try:
            imgs = page.query_selector_all(selector)
            for img in imgs:
                if len(image_urls) >= max_images:
                    break
                src = img.get_attribute("data-src") or img.get_attribute("src")
                # 过滤有效图片链接
                if src and src.startswith("http") and not src.endswith(".svg"):
                    # 排除小图标
                    width = img.get_attribute("width") or ""
                    height = img.get_attribute("height") or ""
                    if width and int(width) < 100:
                        continue
                    if height and int(height) < 100:
                        continue
                    image_urls.append(src)
            if image_urls:
                break
        except:
            continue
    return image_urls


def _save_article(title, content, image_urls, output_root, source_type):
    """保存文章到目录"""
    # 创建输出目录
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_title = "".join([c for c in title if c.isalnum() or c in (" ", "-", "_")])[:30].strip()
    article_dir = output_root / f"{timestamp}_{source_type}_{safe_title}"
    article_dir.mkdir(parents=True, exist_ok=True)
    
    # 下载图片
    downloaded_images = []
    for i, img_url in enumerate(image_urls):
        try:
            ext = "png"
            img_path = article_dir / f"img_{i + 1}.{ext}"
            
            req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response, open(img_path, "wb") as out_file:
                out_file.write(response.read())
            
            downloaded_images.append(str(img_path.resolve()))
            print(f"  下载图片: {img_path.name}")
        except Exception as e:
            print(f"  图片下载失败: {e}")
    
    # 保存正文
    with open(article_dir / "content.txt", "w", encoding="utf-8") as f:
        f.write(content)
    
    # 保存元数据
    with open(article_dir / "meta.txt", "w", encoding="utf-8") as f:
        f.write(f"标题: {title}\n")
        f.write(f"来源: {source_type}\n")
        f.write(f"图片数: {len(downloaded_images)}\n")
    
    print(f"✅ 文章抓取完成: {title}")
    print(f"   保存目录: {article_dir}")
    print(f"   图片数: {len(downloaded_images)}")
    
    return title, content, downloaded_images, article_dir
