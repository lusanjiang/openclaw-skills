#!/usr/bin/env python3
"""
即梦AI图片生成 - 火山引擎官方SDK版
"""

import sys
import json
import os

# 激活虚拟环境
venv_path = '/root/.openclaw/skills/ecommerce-pack/venv'
if os.path.exists(venv_path):
    sys.path.insert(0, f"{venv_path}/lib/python3.12/site-packages")

from volcengine.visual.VisualService import VisualService

def generate_image(prompt, width=1024, height=1024):
    """调用即梦AI生成图片"""
    
    # 读取凭证
    try:
        with open('/root/.openclaw/.volc_access_key', 'r') as f:
            ak = f.read().strip()
        with open('/root/.openclaw/.volc_secret_key', 'r') as f:
            sk_encoded = f.read().strip()
            # Base64解码
            import base64
            sk = base64.b64decode(sk_encoded).decode('utf-8')
    except Exception as e:
        return {"success": False, "error": f"读取凭证失败: {e}"}
    
    # 初始化服务
    visual_service = VisualService()
    visual_service.set_ak(ak)
    visual_service.set_sk(sk)
    
    # 请求参数
    req = {
        "req_key": "jimeng_high_aes_general_v21_L",
        "prompt": prompt,
        "width": width,
        "height": height,
        "seed": -1,
        "use_prompt_augment": True
    }
    
    try:
        resp = visual_service.cv_process(req)
        
        if resp.get("code") == 10000:
            image_urls = resp.get("data", {}).get("image_urls", [])
            return {
                "success": True,
                "image_url": image_urls[0] if image_urls else None,
                "prompt": prompt,
                "request_id": resp.get("request_id")
            }
        else:
            return {
                "success": False,
                "error": resp.get("message", "API调用失败"),
                "code": resp.get("code")
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_product_image(product, background="白色"):
    """生成电商产品图"""
    prompt = f"{background}背景，{product}，极简设计，专业产品摄影，45度角展示，柔和自然光，8K超高清，电商主图风格"
    return generate_image(prompt)


if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "蓝牙耳机"
    print(f"🎨 正在生成: {product}")
    result = generate_product_image(product)
    print(json.dumps(result, ensure_ascii=False, indent=2))
