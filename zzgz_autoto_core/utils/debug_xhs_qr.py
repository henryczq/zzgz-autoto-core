"""
小红书二维码调试工具
用于测试和优化小红书平台的二维码捕获逻辑
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from playwright.sync_api import sync_playwright
import time
from platforms.config import get_platform_url

def debug_xhs_qr():
    """调试小红书二维码捕获"""
    url = get_platform_url('xiaohongshu')
    print(f"🔍 调试小红书二维码捕获")
    print(f"🌐 目标地址: {url}")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 可视化模式便于调试
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            # 访问页面
            print("📥 访问小红书创作者平台...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            
            # 分析页面结构
            print("\n📋 页面元素分析:")
            
            # 查找所有按钮
            buttons = page.query_selector_all('button')
            print(f"发现 {len(buttons)} 个按钮")
            
            # 查找所有图片
            images = page.query_selector_all('img')
            print(f"发现 {len(images)} 张图片")
            
            # 查找特定文本
            print("\n📝 查找关键文本:")
            try:
                login_text = page.wait_for_selector('div:has-text("APP扫一扫登录")', timeout=2000)
                if login_text:
                    print("✅ 找到'APP扫一扫登录'文本!")
                    login_text.evaluate("""element => {
                        element.style.border = '3px solid orange';
                        element.style.backgroundColor = 'yellow';
                        element.scrollIntoView({behavior: 'smooth'});
                    }""")
            except:
                print("❌ 未找到'APP扫一扫登录'文本")
            
            # 查找特定CSS类
            print("\n🎨 查找特定CSS类:")
            css_classes = ['css-dvxtzn', 'css-a7k849', 'css-1lhmg90', 'css-1d81qt0']
            for cls in css_classes:
                elements = page.query_selector_all(f'.{cls}')
                if elements:
                    print(f"✅ 找到类名 '{cls}' 的元素: {len(elements)} 个")
                    for i, elem in enumerate(elements[:2]):  # 只高亮前2个
                        elem.evaluate(f"""element => {{
                            element.style.border = '2px solid purple';
                            console.log('Element {cls} #{i}:', element);
                        }}""")
            
            # 查找base64图片
            base64_images = []
            for img in images:
                src = img.get_attribute('src') or ''
                if src.startswith('data:image'):
                    base64_images.append(src[:100] + '...')
            
            print(f"Base64格式图片: {len(base64_images)} 个")
            if base64_images:
                for i, src in enumerate(base64_images[:3]):
                    print(f"  图片{i+1}: {src}")
            
            # 尝试点击可能的二维码按钮
            print("\n🖱️  尝试点击可能的二维码按钮:")
            
            # 方法1: 通过CSS类名
            button_selectors = [
                'button.css-wemwzq',
                '[class*="wemwzq"]',
                '.login-btn',
                '.qr-toggle-btn',
                '.scan-login-btn'
            ]
            
            for selector in button_selectors:
                try:
                    button = page.wait_for_selector(selector, timeout=2000)
                    if button:
                        print(f"✅ 找到按钮: {selector}")
                        # 高亮显示
                        page.evaluate(f"""() => {{
                            const element = document.querySelector('{selector}');
                            if (element) {{
                                element.style.border = '3px solid red';
                                element.scrollIntoView({{behavior: 'smooth'}});
                            }}
                        }}""")
                        input("按回车键继续...")
                        break
                except:
                    print(f"❌ 未找到: {selector}")
            
            # 方法2: 通过图片特征
            print("\n🔍 通过图片特征查找:")
            for img in images:
                src = img.get_attribute('src') or ''
                if 'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHL' in src:
                    print("✅ 找到目标二维码按钮图片!")
                    # 高亮显示
                    img.evaluate("""img => {
                        img.style.border = '3px solid blue';
                        img.scrollIntoView({behavior: 'smooth'});
                    }""")
                    
                    # 查找父级按钮
                    parent_btn = img.evaluate_handle("""img => {
                        let parent = img.parentElement;
                        while (parent && parent.tagName !== 'BUTTON') {
                            parent = parent.parentElement;
                        }
                        return parent;
                    }""")
                    
                    if parent_btn:
                        print("✅ 找到父级按钮元素")
                        parent_btn.evaluate("""btn => {
                            btn.style.border = '3px solid green';
                        }""")
                    
                    input("按回车键点击按钮...")
                    
                    # 点击按钮
                    if parent_btn:
                        parent_btn.click()
                    else:
                        img.click()
                    
                    print("🖱️  已点击按钮，等待二维码加载...")
                    time.sleep(3)
                    break
            
            # 查找二维码元素
            print("\n🔍 查找二维码元素:")
            qr_selectors = [
                'img[src*="qrcode"]',
                '[class*="qrcode"] img',
                '.login-qr img',
                '.qr-code img',
                '.qrcode-container img'
            ]
            
            for selector in qr_selectors:
                try:
                    qr_img = page.wait_for_selector(selector, timeout=2000)
                    if qr_img:
                        print(f"✅ 找到二维码: {selector}")
                        qr_img.evaluate("""img => {
                            img.style.border = '3px solid purple';
                            img.scrollIntoView({behavior: 'smooth'});
                        }""")
                        input("找到二维码! 按回车键结束...")
                        return True
                except:
                    print(f"❌ 未找到: {selector}")
            
            print("⚠️  未找到二维码元素")
            input("按回车键结束调试...")
            
        except Exception as e:
            print(f"❌ 调试过程中出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_xhs_qr()