#!/usr/bin/env python3
"""
即梦AI 4.0 图片生成 - 火山引擎API
文档: https://www.volcengine.com/docs/85621/1820192
"""

import requests
import json
import sys
import hashlib
import hmac
from datetime import datetime, timezone

def get_credentials():
    """获取API凭证"""
    try:
        with open('/root/.openclaw/.volc_access_key', 'r') as f:
            ak = f.read().strip()
        with open('/root/.openclaw/.volc_secret_key', 'r') as f:
            import base64
            sk_b64 = f.read().strip()
            # 如果已经是明文，直接使用；如果是base64，解码
            try:
                sk = base64.b64decode(sk_b64).decode('utf-8')
            except:
                sk = sk_b64
        return ak, sk
    except Exception as e:
        print(f"❌ 读取凭证失败: {e}")
        return None, None

def hmac_sha256(key, msg):
    """HMAC-SHA256"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_v4(ak, sk, method, host, uri, query, headers, body):
    """
    火山引擎签名V4版本
    """
    now = datetime.now(timezone.utc)
    x_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')
    
    service = "cv"
    region = "cn-north-1"
    
    # Step 1: 规范请求
    http_method = method.upper()
    canonical_uri = uri if uri else '/'
    canonical_querystring = query if query else ''
    
    # Headers
    signed_headers = ['host', 'x-date']
    canonical_headers = f"host:{host}\nx-date:{x_date}\n"
    signed_headers_str = ';'.join(signed_headers)
    
    # Body hash
    payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    
    canonical_request = f"{http_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers_str}\n{payload_hash}"
    
    # Step 2: 待签名字符串
    algorithm = 'HMAC-SHA256'
    credential_scope = f"{date_stamp}/{region}/{service}/request"
    string_to_sign = f"{algorithm}\n{x_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    # Step 3: 签名
    k_date = hmac_sha256(sk.encode('utf-8'), date_stamp)
    k_region = hmac_sha256(k_date, region)
    k_service = hmac_sha256(k_region, service)
    k_signing = hmac_sha256(k_service, 'request')
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # Step 4: Authorization
    authorization = f"{algorithm} Credential={ak}/{credential_scope}, SignedHeaders={signed_headers_str}, Signature={signature}"
    
    return authorization, x_date

def generate_image_4x(prompt, width=1024, height=1024):
    """
    调用即梦4.0生成图片
    """
    
    ak, sk = get_credentials()
    if not ak or not sk:
        return {"success": False, "error": "API凭证未配置"}
    
    # API配置 - 即梦4.0
    host = "visual.volcengineapi.com"
    method = "POST"
    uri = "/"
    query = "Action=CVProcess&Version=2022-08-31"
    url = f"https://{host}/?{query}"
    
    # 请求体 - 即梦4.0模型
    payload = {
        "req_key": "high_aes_general_v40_L",  # 即梦4.0模型
        "prompt": prompt,
        "width": width,
        "height": height,
        "seed": -1,
        "logo_info": {
            "add_logo": True,
            "logo_text_content": "AI Generated"
        }
    }
    body = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    
    # 签名
    authorization, x_date = get_signature_v4(ak, sk, method, host, uri, query, {}, body)
    
    # 请求头
    headers = {
        'Host': host,
        'X-Date': x_date,
        'Content-Type': 'application/json',
        'Authorization': authorization
    }
    
    try:
        resp = requests.post(url, headers=headers, data=body.encode('utf-8'), timeout=60)
        
        print(f"Status: {resp.status_code}")
        
        data = resp.json()
        
        if resp.status_code == 200:
            # 检查响应结构
            if 'ResponseMetadata' in data:
                error = data['ResponseMetadata'].get('Error', {})
                if error:
                    return {
                        "success": False,
                        "error": error.get('Message', 'API错误'),
                        "code": error.get('Code')
                    }
            
            # 获取图片URL
            result = data.get('Result', data)
            image_urls = result.get('image_urls', [])
            if not image_urls and 'data' in result:
                image_urls = result['data'].get('image_urls', [])
            
            return {
                "success": True,
                "image_url": image_urls[0] if image_urls else None,
                "prompt": prompt,
                "raw_response": data
            }
        else:
            return {
                "success": False,
                "error": f"HTTP错误: {resp.status_code}",
                "detail": data
            }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def generate_product_image(product, background="白色"):
    """生成电商产品图"""
    prompt = f"{background}背景，{product}，极简设计，专业产品摄影，45度角展示，柔和自然光，8K超高清，电商主图风格，纯净白色背景，产品居中构图"
    return generate_image_4x(prompt)

def main():
    product = sys.argv[1] if len(sys.argv) > 1 else "白色背景，蓝牙耳机"
    print(f"🎨 即梦4.0 正在生成: {product}")
    print("=" * 50)
    
    result = generate_product_image(product)
    print()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

if __name__ == "__main__":
    main()
