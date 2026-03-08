"""
验证认证文件配置的脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from platforms import AUTH_FILES, get_auth_status

def verify_auth_config():
    """验证认证文件配置"""
    print("🔍 认证文件配置验证")
    print("=" * 40)
    
    print("\n📋 平台认证文件映射:")
    for platform, filename in AUTH_FILES.items():
        print(f"  {platform:12} -> {filename}")
    
    print("\n📂 实际文件路径检查:")
    status = get_auth_status()
    for platform, info in status.items():
        filepath = info['file']
        exists = "✅ 存在" if info.get('exists', False) else "❌ 不存在"
        print(f"  {platform:12} -> {filepath} {exists}")
    
    print("\n✅ 配置验证完成!")

if __name__ == "__main__":
    verify_auth_config()