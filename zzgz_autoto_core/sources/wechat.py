import time
import urllib.request
from pathlib import Path


def scrape_article(page, url, output_root, max_images=3):
    """抓取微信公众号文章"""
    print(f"正在抓取微信文章: {url}")
    
    page.goto(url)
    # 等待页面加载，这里放宽一点限制，避免某些资源加载超时导致整体失败
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except:
        print("页面加载超时(networkidle)，尝试继续...")

    # 尝试处理可能的验证页面或加载延迟
    # 如果找不到标题，可能是被反爬拦截了
    try:
        page.wait_for_selector("#activity-name", timeout=10000)
    except Exception as e:
        print(f"未找到文章标题元素，可能是被拦截或页面加载失败: {e}")
        # 保存截图和HTML以便调试
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        debug_dir = output_root / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        screenshot_path = debug_dir / f"error_{timestamp}.png"
        html_path = debug_dir / f"error_{timestamp}.html"
        
        page.screenshot(path=screenshot_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
            
        print(f"已保存错误截图: {screenshot_path}")
        print(f"已保存错误页面HTML: {html_path}")
        raise e

    # 获取标题
    title = page.inner_text("#activity-name").strip()

    # 获取正文
    content = page.inner_text("#js_content").strip()

    # 获取图片
    # 微信图片通常在 img 标签的 data-src 属性中
    img_elements = page.query_selector_all("#js_content img")
    image_urls = []
    for img in img_elements:
        src = img.get_attribute("data-src") or img.get_attribute("src")
        if src and "mmbiz.qpic.cn" in src:
            image_urls.append(src)
        if len(image_urls) >= max_images:
            break

    # 创建输出目录
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_title = "".join([c for c in title if c.isalnum() or c in (" ", "-", "_")])[:30].strip()
    article_dir = output_root / f"{timestamp}_{safe_title}"
    article_dir.mkdir(parents=True, exist_ok=True)

    # 下载图片
    downloaded_images = []
    for i, img_url in enumerate(image_urls):
        try:
            ext = "png"
            img_path = article_dir / f"img_{i + 1}.{ext}"

            # 使用 urllib 下载图片，避免引入新依赖
            req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response, open(img_path, "wb") as out_file:
                out_file.write(response.read())

            downloaded_images.append(str(img_path.resolve()))
        except Exception as e:
            print(f"图片下载失败: {e}")

    # 保存原始正文
    with open(article_dir / "content.txt", "w", encoding="utf-8") as f:
        f.write(content)

    return title, content, downloaded_images, article_dir
