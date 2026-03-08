import argparse
import sys
import platform

try:
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
except Exception:
    print("未检测到 Playwright，请先手动安装：pip install playwright，然后执行 playwright install chromium")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="检查 Playwright 与 Chromium 安装情况")
    parser.add_argument("--headless", action="store_true", help="无头模式运行（Ubuntu服务器推荐）")
    args = parser.parse_args()
    
    # Ubuntu服务器自动启用无头模式
    if platform.system().lower() == 'linux' and not args.headless:
        print("🐧 检测到Linux系统，自动启用无头模式")
        args.headless = True

    try:
        print(f"运行模式: {'无头模式' if args.headless else '可视化模式'}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.headless)
            browser.close()
        print("Playwright 与 Chromium 可用")
    except PlaywrightError as exc:
        msg = str(exc)
        if "Executable doesn't exist" in msg or "chromium" in msg.lower():
            print("未检测到 Chromium，请手动执行：playwright install chromium")
        else:
            print(f"Playwright/Chromium 启动失败：{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
