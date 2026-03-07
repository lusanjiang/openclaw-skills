#!/usr/bin/env python3
"""
即梦AI图片生成 - 火山引擎API完整签名实现
参考: https://www.volcengine.com/docs/6444/69874
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
            sk = base64.b64decode(sk_b64).decode('utf-8')
        return ak, sk
    except Exception as e:
        print(f"❌ 读取凭证失败: {e}")
        return None, None

def hmac_sha256(key, msg):
    """HMAC-SHA256"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature(ak, sk, service, region, method, uri, query, headers, body):
    """
    计算火山引擎API签名
    参考: https://www.volcengine.com/docs/6444/69874
    """
    # 时间戳
    now = datetime.now(timezone.utc)
    x_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')
    
    # Step 1: 创建规范请求
    # HTTP方法
    http_method = method.upper()
    
    # 规范URI
    canonical_uri = uri if uri else '/'
    
    # 规范查询字符串
    canonical_querystring = query if query else ''
    
    # 规范Headers
    # 必须包含host和x-date
    signed_headers = ['host', 'x-date']
    canonical_headers = ''
    for key in signed_headers:
        if key in headers:
            canonical_headers += f"{key}:{headers[key]}\n"
    signed_headers_str = ';'.join(signed_headers)
    
    # 请求体哈希
    if body:
        payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    else:
        payload_hash = hashlib.sha256(b'').hexdigest()
    
    # 组合规范请求
    canonical_request = f"{http_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers_str}\n{payload_hash}"
    
    # Step 2: 创建待签名字符串
    algorithm = 'HMAC-SHA256'
    credential_scope = f"{date_stamp}/{region}/{service}/request"
    string_to_sign = f"{algorithm}\n{x_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    # Step 3: 计算签名
    k_date = hmac_sha256(sk.encode('utf-8'), date_stamp)
    k_region = hmac_sha256(k_date, region)
    k_service = hmac_sha256(k_region, service)
    k_signing = hmac_sha256(k_service, 'request')
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # Step 4: 构建Authorization头
    authorization = f"{algorithm} Credential={ak}/{credential_scope}, SignedHeaders={signed_headers_str}, Signature={signature}"
    
    return authorization, x_date

def generate_image(prompt, width=1024, height=1024):
    """调用即梦AI生成图片"""
    
    ak, sk = get_credentials()
    if not ak or not sk:
        return {"success": False, "error": "API凭证未配置"}
    
    # API配置
    service = "cv"
    region = "cn-north-1"
    host = "visual.volcengineapi.com"
    method = "POST"
    uri = "/"
    query = "Action=CVProcess&Version=2022-08-31"
    url = f"https://{host}/?{query}"
    
    # 请求体
    payload = {
        "req_key": "jimeng_high_aes_general_v21_L",
        "prompt": prompt,
        "width": width,
        "height": height,
        "seed": -1,
        "use_prompt_augment": True
    }
    body = json.dumps(payload, separators=(',', ':'))
    
    # 准备Headers
    headers = {
        'host': host,
        'content-type': 'application/json'
    }
    
    # 计算签名
    authorization, x_date = get_signature(ak, sk, service, region, method, uri, query, headers, body)
    
    # 完整请求头
    request_headers = {
        'Host': host,
        'X-Date': x_date,
        'Content-Type': 'application/json',
        'Authorization': authorization
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: {json.dumps(request_headers, indent=2)}")
    print(f"Request Body: {body}")
    
    try:
        resp = requests.post(url, headers=request_headers, data=body, timeout=60)
        print(f"Response Status: {resp.status_code}")
        print(f"Response: {resp.text[:1000]}")
        
        data = resp.json()
        
        if resp.status_code == 200:
            response_metadata = data.get('ResponseMetadata', {})
            error = response_metadata.get('Error', {})
            if error:
                return {
                    "success": False,
                    "error": error.get('Message', 'API错误'),
                    "code": error.get('Code')
                }
            
            result_data = data.get('Result', {}).get('data', {})
            image_urls = result_data.get('image_urls', [])
            return {
                "success": True,
                "image_url": image_urls[0] if image_urls else None,
                "prompt": prompt
            }
        else:
            return {
                "success": False,
                "error": f"HTTP错误: {resp.status_code}",
                "detail": resp.text[:500]
            }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def main():
    product = sys.argv[1] if len(sys.argv) > 1 else "白色背景，蓝牙耳机"
    print(f"🎨 正在生成: {product}")
    print("=" * 50)
    
    result = generate_image(product)
    print()
    print("Result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
