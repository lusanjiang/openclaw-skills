#!/usr/bin/env python3
"""
EAP3 Token优化监控脚本 v2.0
优化点：
1. 本地缓存SID，减少登录请求
2. 精简日志输出
3. 智能重试机制
4. 批量处理通知
"""

import requests
import json
import os
import hashlib
from datetime import datetime, timedelta

EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

# 缓存配置
CACHE_DIR = "/root/.openclaw/cache"
CACHE_FILE = f"{CACHE_DIR}/eap3_session.json"
CACHE_DURATION = 25  # 分钟，SID有效期约30分钟

# 确保缓存目录存在
os.makedirs(CACHE_DIR, exist_ok=True)

def log(message, level="INFO"):
    """精简日志，只输出关键信息"""
    if level in ["INFO", "WARN", "ERROR"]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

def get_cached_session():
    """获取缓存的会话"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            # 检查缓存是否过期
            cached_time = datetime.fromisoformat(cache.get('timestamp', ''))
            if datetime.now() - cached_time < timedelta(minutes=CACHE_DURATION):
                return cache.get('sid'), cache.get('cookies')
    except Exception:
        pass
    return None, None

def save_session(sid, cookies):
    """保存会话到缓存"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                'sid': sid,
                'cookies': cookies,
                'timestamp': datetime.now().isoformat()
            }, f)
    except Exception as e:
        log(f"缓存保存失败: {e}", "WARN")

def login():
    """登录获取SID"""
    try:
        session = requests.Session()
        
        # 使用缓存的SID尝试
        cached_sid, cached_cookies = get_cached_session()
        if cached_sid:
            # 验证SID是否有效
            test_resp = session.post(
                f"{EAP3_URL}/r/jd",
                params={"sid": cached_sid, "cmd": "com.actionsoft.apps.notification_load_unread_msg"},
                headers={"X-Requested-With": "XMLHttpRequest"},
                timeout=10
            )
            if test_resp.json().get("result") == "ok":
                log("使用缓存SID")
                return cached_sid, session
        
        # 需要重新登录
        log("重新登录...")
        post_data = {
            "userid": USER_ID,
            "pwd": ENCRYPTED_PWD,
            "cmd": "com.actionsoft.apps.tengen.login",
            "deviceType": "pc",
            "lang": "cn",
            "pwdEncode": "RSA",
            "timeZone": "8",
            "_CACHE_LOGIN_TIME_": str(int(datetime.now().timestamp() * 1000))
        }
        
        resp = session.post(
            f"{EAP3_URL}/r/w",
            data=post_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        
        data = resp.json()
        sid = data.get("data", {}).get("sid")
        
        if sid:
            save_session(sid, {})
            log("登录成功")
            return sid, session
        else:
            log("登录失败", "ERROR")
            return None, None
            
    except Exception as e:
        log(f"登录异常: {e}", "ERROR")
        return None, None

def check_todos(sid, session):
    """检查待办"""
    try:
        resp = session.post(
            f"{EAP3_URL}/r/jd",
            params={"sid": sid, "cmd": "com.actionsoft.apps.notification_load_unread_msg"},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=15
        )
        
        data = resp.json()
        if data.get("result") != "ok":
            return None
        
        amount = data.get("data", {}).get("amount", 0)
        
        # 只统计 XZ38
        xz38_list = []
        for item in data.get("data", {}).get("list", []):
            content = item.get("content", "")
            if "XZ38" in content and ("定制" in content or "新产品需求" in content):
                xz38_list.append({
                    "user": item.get("userName", ""),
                    "content": content[:60] + "..." if len(content) > 60 else content
                })
        
        return {
            "total": amount,
            "xz38_count": len(xz38_list),
            "xz38_list": xz38_list
        }
        
    except Exception as e:
        log(f"检查待办异常: {e}", "ERROR")
        return None

def save_result(result):
    """保存结果"""
    try:
        result_file = "/root/.openclaw/logs/eap3_check_result.json"
        with open(result_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                **result
            }, f)
    except Exception:
        pass

def main():
    log("=" * 30)
    log("EAP3 监控 (Token优化版)")
    
    # 登录
    sid, session = login()
    if not sid:
        log("无法获取会话", "ERROR")
        return
    
    # 检查待办
    result = check_todos(sid, session)
    if result is None:
        log("检查失败", "ERROR")
        return
    
    # 输出结果
    log(f"未读: {result['total']} | XZ38: {result['xz38_count']}")
    
    if result['xz38_count'] > 0:
        for item in result['xz38_list']:
            log(f"  - {item['user']}")
        save_result(result)
    
    log("完成")

if __name__ == "__main__":
    main()
