#!/usr/bin/env python3
"""
即梦AI图片生成 - 使用API易简化接入
API文档: https://docs.apiyi.com/
"""

import requests
import json
import sys
import os

def get_api_key():
    """获取API Key"""
    try:
        with open('/root/.openclaw/.volc_access_key', 'r') as f:
            return f.read().strip()
    except:
        return None

def generate_image(prompt, width=1024, height=1024):
    """
    调用即梦AI生成图片
    
    使用API易的OpenAI兼容接口
    """
    
    api_key = get_api_key()
    if not api_key:
        return {"success": False, "error": "API Key未配置"}
    
    # API易即梦接口
    url = "https://api.apiyi.com/v1/images/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "jimeng-4.0",
        "prompt": prompt,
        "size": f"{width}x{height}",
        "n": 1
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        data = response.json()
        
        if response.status_code == 200 and data.get("data"):
            return {
                "success": True,
                "image_url": data["data"][0].get("url"),
                "prompt": prompt
            }
        else:
            return {
                "success": False,
                "error": f"API错误: {data.get('error', {}).get('message', '未知错误')}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def generate_product_image(product, background="白色", style="简约"):
    """生成电商产品图"""
    
    # 专业电商提示词
    prompt = f"{background}背景，{product}，极简设计，专业产品摄影，45度角展示，柔和自然光，细腻阴影，8K超高清，电商主图风格，纯净背景，产品居中构图"
    
    return generate_image(prompt)


def main():
    if len(sys.argv) > 1:
        product = ' '.join(sys.argv[1:])
    else:
        product = input("请输入产品名称: ")
    
    print(f"🎨 正在生成: {product}")
    result = generate_product_image(product)
    
    if result["success"]:
        print(f"✅ 成功! 图片URL: {result['image_url']}")
    else:
        print(f"❌ 失败: {result['error']}")


if __name__ == "__main__":
    main()
