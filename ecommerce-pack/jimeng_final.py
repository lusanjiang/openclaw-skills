#!/usr/bin/env python3
"""
即梦AI 4.0 - 电商运营技能包
已配置Ark平台API
Endpoint: ep-20260307113729-4v77p
"""

import requests
import json
import os

class JimengAI:
    """即梦AI图片生成器 - Ark平台API版"""
    
    def __init__(self):
        self.api_key = self._load_key('/root/.openclaw/.ark_api_key')
        self.endpoint_id = "ep-20260307113729-4v77p"  # Jimeng-Seedream-4
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
    
    def _load_key(self, path):
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except:
            return None
    
    def generate(self, prompt, width=1024, height=1024):
        """生成图片"""
        
        if not self.api_key:
            return {"success": False, "error": "API Key未配置"}
        
        url = f"{self.base_url}/images/generations"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.endpoint_id,
            "prompt": prompt,
            "size": f"{width}x{height}",
            "n": 1
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            data = resp.json()
            
            if resp.status_code == 200 and data.get("data"):
                return {
                    "success": True,
                    "image_url": data["data"][0].get("url"),
                    "prompt": prompt
                }
            else:
                return {
                    "success": False,
                    "error": data.get("error", {}).get("message", "API调用失败")
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


def generate_product_image(product, background="白色"):
    """生成电商产品图"""
    ai = JimengAI()
    prompt = f"{background}背景，{product}，极简设计，专业产品摄影，45度角展示，柔和自然光，8K超高清，电商主图风格"
    return ai.generate(prompt)


if __name__ == "__main__":
    import sys
    product = sys.argv[1] if len(sys.argv) > 1 else "蓝牙耳机"
    print(f"🎨 即梦AI生成: {product}")
    print("=" * 50)
    
    result = generate_product_image(product)
    print(json.dumps(result, ensure_ascii=False, indent=2))
