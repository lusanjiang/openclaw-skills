#!/usr/bin/env python3
"""
即梦AI图片生成 - 通过Ark平台OpenAI兼容接口
Ark文档: https://www.volcengine.com/docs/82379/1263512
"""

import requests
import json
import sys

def get_api_key():
    """获取API Key"""
    try:
        with open('/root/.openclaw/.volc_access_key', 'r') as f:
            return f.read().strip()
    except:
        return None

def generate_image(prompt, width=1024, height=1024):
    """
    调用即梦AI生成图片 - 通过Ark平台
    """
    
    api_key = get_api_key()
    if not api_key:
        return {"success": False, "error": "API Key未配置"}
    
    # Ark平台OpenAI兼容接口
    url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "jimeng-4.0",  # 即梦4.0模型
        "prompt": prompt,
        "size": f"{width}x{height}",
        "n": 1,
        "response_format": "url"
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        data = resp.json()
        
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")
        
        if resp.status_code == 200:
            if data.get("data") and len(data["data"]) > 0:
                return {
                    "success": True,
                    "image_url": data["data"][0].get("url"),
                    "prompt": prompt
                }
            else:
                return {
                    "success": False,
                    "error": "API返回数据格式错误",
                    "detail": data
                }
        else:
            return {
                "success": False,
                "error": f"HTTP错误: {resp.status_code}",
                "detail": data.get("error", {}).get("message", resp.text)
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_product_image(product, background="白色"):
    """生成电商产品图"""
    prompt = f"{background}背景，{product}，极简设计，专业产品摄影，45度角展示，柔和自然光，8K超高清，电商主图风格，纯净白色背景，产品居中构图"
    return generate_image(prompt)

def main():
    product = sys.argv[1] if len(sys.argv) > 1 else "白色背景，蓝牙耳机"
    print(f"🎨 Ark平台即梦AI 正在生成: {product}")
    print("=" * 50)
    
    result = generate_product_image(product)
    print()
    print("Result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
