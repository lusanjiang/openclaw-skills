#!/usr/bin/env python3
"""
即梦AI 4.0 - 通过Ark平台OpenAI兼容接口
需要: Endpoint ID 和 API Key
"""

import requests
import json
import sys

def generate_image(endpoint_id, api_key, prompt, width=1024, height=1024):
    """
    调用即梦4.0生成图片
    
    Args:
        endpoint_id: Ark平台终端节点ID (如: ep-202xxxxx)
        api_key: Ark平台API Key (如: 0d1f2e3c-xxxx)
        prompt: 提示词
    """
    
    url = f"https://ark.cn-beijing.volces.com/api/v3/images/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": endpoint_id,  # 使用endpoint_id作为model
        "prompt": prompt,
        "size": f"{width}x{height}"
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        data = resp.json()
        
        if resp.status_code == 200:
            if data.get("data"):
                return {
                    "success": True,
                    "image_url": data["data"][0].get("url"),
                    "prompt": prompt
                }
            else:
                return {"success": False, "error": "无图片数据", "detail": data}
        else:
            return {
                "success": False, 
                "error": f"HTTP {resp.status_code}",
                "detail": data.get("error", {}).get("message", str(data))
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    print("🎨 即梦AI 4.0 - Ark平台接口")
    print("=" * 50)
    print()
    print("⚠️  需要配置Ark平台凭证:")
    print()
    print("1. Endpoint ID (终端节点ID)")
    print("   格式: ep-202xxxxx")
    print()
    print("2. API Key")
    print("   格式: 0d1f2e3c-xxxx")
    print()
    print("获取方式:")
    print("1. 访问 https://console.volcengine.com/ark/")
    print("2. 进入「终端节点」创建即梦4.0端点")
    print("3. 进入「API Key管理」创建Key")
    print()
    print("配置后我就能自动调用即梦AI生成图片")


if __name__ == "__main__":
    main()
