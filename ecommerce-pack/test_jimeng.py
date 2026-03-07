#!/root/.openclaw/skills/ecommerce-pack/venv/bin/python
"""
即梦AI 4.0 - 火山引擎SDK直接调用
"""

import sys
sys.path.insert(0, '/root/.openclaw/skills/ecommerce-pack/venv/lib/python3.12/site-packages')

from volcengine.visual.VisualService import VisualService
import json

def main():
    # 读取凭证
    with open('/root/.openclaw/.volc_access_key', 'r') as f:
        ak = f.read().strip()
    with open('/root/.openclaw/.volc_secret_key', 'r') as f:
        sk = f.read().strip()
    
    print(f"AK: {ak[:25]}...")
    print(f"SK: {sk[:20]}...")
    print()
    
    # 初始化服务
    visual_service = VisualService()
    visual_service.set_ak(ak)
    visual_service.set_sk(sk)
    
    # 请求参数
    req = {
        "req_key": "high_aes_general_v40_L",
        "prompt": "白色背景，蓝牙耳机，极简设计，专业产品摄影",
        "width": 1024,
        "height": 1024,
        "seed": -1
    }
    
    print("🎨 正在调用即梦4.0 API...")
    print()
    
    try:
        resp = visual_service.cv_process(req)
        print(f"✅ 调用成功!")
        print(f"响应: {json.dumps(resp, indent=2, default=str)[:2000]}")
    except Exception as e:
        print(f"❌ 调用失败: {e}")

if __name__ == "__main__":
    main()
