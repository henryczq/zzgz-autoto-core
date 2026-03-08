import time


# 小红书发布页很吃“节奏”：跳转/异步渲染时连续快速点击很容易失效。
# 这些等待用于让界面稳定后再操作。


def _ui_settle(page, wait_ms: int, reason: str = ""):
    """等待页面/组件稳定，避免连续频繁操作导致点击丢失。"""
    if reason:
        print(f"等待界面稳定：{reason}（{wait_ms}ms）")
    try:
        page.wait_for_load_state("domcontentloaded", timeout=4000)
    except Exception:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=4000)
    except Exception:
        pass
    try:
        page.wait_for_timeout(wait_ms)
    except Exception:
        time.sleep(max(0.0, wait_ms / 1000))


def _fill_richtext(page, editor_loc, text: str, *, clear_first: bool = True, is_html: bool = None):
    """给 contenteditable/富文本编辑器稳定输入。

    适用场景：ProseMirror/Tiptap、Quill(ql-editor) 等。
    说明：Playwright 的 locator.fill() 只适用于 input/textarea，富文本一般需要 click + keyboard。
    
    参数:
        page: Playwright page 对象
        editor_loc: 编辑器 locator
        text: 要输入的文本或 HTML
        clear_first: 是否先清空编辑器
        is_html: 是否为 HTML 格式（True 时使用剪贴板粘贴方式，None 则自动检测）
    """
    if editor_loc is None:
        raise Exception("editor locator is None")

    try:
        editor_loc.first.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass

    # 尽量让编辑器获得焦点
    try:
        editor_loc.first.click(force=True, timeout=5000)
    except Exception:
        try:
            editor_loc.first.dispatch_event("click")
        except Exception:
            pass

    if clear_first:
        try:
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass

    text = text or ""
    if text:
        # 自动检测是否为 HTML
        if is_html is None:
            is_html = text.strip().startswith('<') and '</' in text
        
        if is_html:
            # 使用 evaluate 直接在编辑器中插入 HTML
            try:
                # 通过 JavaScript 直接设置编辑器内容
                page.evaluate("""
                    (html) => {
                        const editor = document.querySelector('[contenteditable="true"]');
                        if (editor) {
                            editor.innerHTML = html;
                            // 触发 input 事件，让编辑器知道内容变化了
                            const event = new Event('input', { bubbles: true });
                            editor.dispatchEvent(event);
                        }
                    }
                """, text)
                page.wait_for_timeout(300)
                print("✅ 已使用 HTML 直接插入方式")
            except Exception as e:
                # 如果 HTML 插入失败，回退到普通文本
                print(f"⚠️ HTML 插入失败，回退到纯文本：{e}")
                page.keyboard.insert_text(text)
        else:
            try:
                page.keyboard.insert_text(text)
            except Exception:
                # insert_text 在少数环境会失败，回退到 type
                page.keyboard.type(text, delay=10)

    try:
        page.wait_for_timeout(200)
    except Exception:
        time.sleep(0.2)
