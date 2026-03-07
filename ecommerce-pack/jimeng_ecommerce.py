#!/usr/bin/env python3
"""
即梦AI图片生成 - 电商运营技能包
已配置火山引擎API
"""

import requests
import json
import os

class JimengAI:
    """即梦AI图片生成器"""
    
    def __init__(self):
        self.access_key = self._load_key('/root/.openclaw/.volc_access_key')
        self.secret_key = self._load_key('/root/.openclaw/.volc_secret_key')
        self.api_endpoint = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    
    def _load_key(self, path):
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except:
            return None
    
    def generate(self, prompt, width=1024, height=1024):
        """生成图片"""
        
        if not self.access_key:
            return {"success": False, "error": "API密钥未配置"}
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_key}"
        }
        
        payload = {
            "model": "jimeng-4.0",
            "prompt": prompt,
            "size": f"{width}x{height}"
        }
        
        try:
            resp = requests.post(self.api_endpoint, headers=headers, json=payload, timeout=60)
            data = resp.json()
            
            if resp.status_code == 200:
                return {
                    "success": True,
                    "image_url": data.get("data", [{}])[0].get("url"),
                    "prompt": prompt
                }
            else:
                return {
                    "success": False,
                    "error": data.get("error", {}).get("message", "API调用失败")
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 快捷函数
def generate_product_image(product, background="白色"):
    """生成电商产品图"""
    ai = JimengAI()
    prompt = f"{background}背景，{product}，极简设计，专业产品摄影，45度角展示，柔和自然光，8K超高清，电商主图风格"
    return ai.generate(prompt)


if __name__ == "__main__":
    import sys
    product = sys.argv[1] if len(sys.argv) > 1 else "蓝牙耳机"
    result = generate_product_image(product)
    print(json.dumps(result, ensure_ascii=False, indent=2))
