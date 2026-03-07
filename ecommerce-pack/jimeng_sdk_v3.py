#!/root/.openclaw/skills/ecommerce-pack/venv/bin/python
"""
即梦AI 4.0 - 使用火山引擎官方SDK
"""

import sys
sys.path.insert(0, '/root/.openclaw/skills/ecommerce-pack/venv/lib/python3.12/site-packages')

from volcengine.visual.VisualService import VisualService
import json
import base64

def get_credentials():
    """获取API凭证"""
    try:
        with open('/root/.openclaw/.volc_access_key', 'r') as f:
            ak = f.read().strip()
        with open('/root/.openclaw/.volc_secret_key', 'r') as f:
            sk_b64 = f.read().strip()
            # 尝试解码base64
            try:
                sk_bytes = base64.b64decode(sk_b64)
                sk = sk_bytes.decode('utf-8')
            except:
                sk = sk_b64
        return ak, sk
    except Exception as e:
        print(f"❌ 读取凭证失败: {e}")
        return None, None

def generate_image(prompt, width=1024, height=1024):
    """调用即梦4.0生成图片"""
    
    ak, sk = get_credentials()
    if not ak or not sk:
        return {"success": False, "error": "API凭证未配置"}
    
    print(f"AK: {ak[:20]}...")
    print(f"SK length: {len(sk)}")
    
    # 初始化VisualService
    visual_service = VisualService()
    visual_service.set_ak(ak)
    visual_service.set_sk(sk)
    
    # 请求参数
    req = {
        "req_key": "high_aes_general_v40_L",
        "prompt": prompt,
        "width": width,
        "height": height,
        "seed": -1,
        "use_prompt_augment": True
    }
    
    try:
        resp = visual_service.cv_process(req)
        
        # 检查响应
        if 'ResponseMetadata' in resp:
            error = resp['ResponseMetadata'].get('Error', {})
            if error:
                return {
                    "success": False,
                    "error": error.get('Message', 'API错误'),
                    "code": error.get('Code')
                }
        
        # 获取图片URL
        result_data = resp.get('data', {})
        if not result_data:
            result_data = resp.get('Result', {}).get('data', {})
        
        image_urls = result_data.get('image_urls', [])
        
        return {
            "success": True,
            "image_url": image_urls[0] if image_urls else None,
            "prompt": prompt
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    product = sys.argv[1] if len(sys.argv) > 1 else "白色背景，蓝牙耳机"
    print(f"🎨 即梦4.0 (SDK版) 正在生成: {product}")
    print("=" * 50)
    
    result = generate_image(product)
    print()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
