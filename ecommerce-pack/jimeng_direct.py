#!/usr/bin/env python3
"""
即梦AI图片生成 - 直接HTTP调用
使用火山引擎官方API
"""

import requests
import json
import sys
import os
import hashlib
import hmac
from datetime import datetime, timezone

def get_credentials():
    """获取API凭证"""
    try:
        with open('/root/.openclaw/.volc_access_key', 'r') as f:
            ak = f.read().strip()
        with open('/root/.openclaw/.volc_secret_key', 'r') as f:
            sk_b64 = f.read().strip()
            import base64
            sk = base64.b64decode(sk_b64).decode('utf-8')
        return ak, sk
    except Exception as e:
        print(f"❌ 读取凭证失败: {e}")
        return None, None


def sign_request(ak, sk, service, region, body):
    """计算签名"""
    now = datetime.now(timezone.utc)
    date_stamp = now.strftime('%Y%m%d')
    
    # 规范请求
    method = 'POST'
    uri = '/'
    query = 'Action=CVProcess&Version=2022-08-31'
    
    # 请求头
    content_type = 'application/json'
    x_date = now.strftime('%Y%m%dT%H%M%SZ')
    
    # 计算body的sha256
    payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    
    # 规范Headers
    canonical_headers = f"content-type:{content_type}\nx-date:{x_date}\n"
    signed_headers = "content-type;x-date"
    
    # 规范请求
    canonical_request = f"{method}\n{uri}\n{query}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    
    # 签名字符串
    algorithm = "HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/request"
    string_to_sign = f"{algorithm}\n{x_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    # 计算签名
    k_date = hmac.new(sk.encode('utf-8'), date_stamp.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, 'request'.encode('utf-8'), hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # Authorization头
    authorization = f"{algorithm} Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    
    return authorization, x_date


def generate_image(prompt, width=1024, height=1024):
    """生成图片"""
    
    ak, sk = get_credentials()
    if not ak or not sk:
        return {"success": False, "error": "API凭证未配置"}
    
    # API配置
    service = "cv"
    region = "cn-north-1"
    host = "visual.volcengineapi.com"
    url = f"https://{host}/?Action=CVProcess&Version=2022-08-31"
    
    # 请求体
    payload = {
        "req_key": "jimeng_high_aes_general_v21_L",
        "prompt": prompt,
        "width": width,
        "height": height,
        "seed": -1,
        "use_prompt_augment": True
    }
    
    body = json.dumps(payload)
    
    # 计算签名
    authorization, x_date = sign_request(ak, sk, service, region, body)
    
    # 请求头
    headers = {
        "Content-Type": "application/json",
        "X-Date": x_date,
        "Authorization": authorization
    }
    
    try:
        resp = requests.post(url, headers=headers, data=body, timeout=60)
        data = resp.json()
        
        if resp.status_code == 200 and data.get("code") == 10000:
            image_urls = data.get("data", {}).get("image_urls", [])
            return {
                "success": True,
                "image_url": image_urls[0] if image_urls else None,
                "prompt": prompt
            }
        else:
            return {
                "success": False,
                "error": data.get("message", "API调用失败"),
                "code": data.get("code")
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    product = sys.argv[1] if len(sys.argv) > 1 else "白色背景 蓝牙耳机"
    print(f"🎨 正在生成: {product}")
    
    result = generate_image(product)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
