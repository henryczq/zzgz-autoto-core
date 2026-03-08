import json
import time
from pathlib import Path


def is_url(string):
    """判断字符串是否为 URL"""
    if not isinstance(string, str):
        return False
    return string.startswith(("http://", "https://"))


def ensure_test_placeholder(skill_dir: Path) -> Path:
    """确保存在测试占位图，如果不存在则生成"""
    test_img_path = skill_dir / "test_placeholder.png"
    if not test_img_path.exists():
        import base64
        # 一个 1x1 像素的红色 PNG 占位图
        img_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        with open(test_img_path, "wb") as f:
            f.write(img_data)
    return test_img_path


def load_article_payload(path: Path):
    """从 JSON 文件加载文章数据"""
    if not path.exists():
        print(f"⚠️ 警告: 文件不存在 - {path}")
        print(f"  当前工作目录: {Path.cwd()}")
        return {}
    print(f"✅ 加载数据文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  📝 标题: {data.get('title', '无')}")
    return data


def save_article_payload(article_dir: Path, title, content, images, source_url=""):
    """保存文章数据到 JSON"""
    payload = {
        "title": title,
        "content": content,
        "images": images,
        "source_url": source_url,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    json_path = article_dir / "article.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return json_path, payload
