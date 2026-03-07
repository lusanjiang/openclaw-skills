#!/usr/bin/env python3
"""
即梦AI图片生成 - 简化版
无需部署服务，直接调用
"""

import requests
import json
import sys

def generate_image(prompt, session_id, width=1024, height=1024):
    """
    调用即梦AI生成图片
    
    Args:
        prompt: 提示词
        session_id: 即梦AI的sessionid
        width: 图片宽度
        height: 图片高度
    """
    
    url = "https://jimeng.jianying.com/mweb/v1/generate_image"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {session_id}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "model": "jimeng-4.0"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "image_url": data.get("data", {}).get("url"),
                "prompt": prompt
            }
        else:
            return {
                "success": False,
                "error": f"请求失败: {response.status_code}",
                "detail": response.text
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    # 示例：生成蓝牙耳机产品图
    prompt = "白色背景，无线蓝牙耳机，极简设计，银色金属质感，45度角展示，柔和自然光，电商主图风格，8K高清"
    
    print("🎨 即梦AI图片生成")
    print("=" * 50)
    print(f"提示词: {prompt}")
    print()
    print("⚠️  需要配置Session ID才能使用")
    print()
    print("获取方式:")
    print("1. 访问 https://jimeng.jianying.com")
    print("2. 用 15576684226 登录")
    print("3. F12 → Application → Cookies → 复制 sessionid")
    print("4. 设置环境变量: export JIMENG_SESSION_ID='你的sessionid'")


if __name__ == "__main__":
    main()
