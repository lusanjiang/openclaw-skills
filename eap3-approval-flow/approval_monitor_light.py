#!/usr/bin/env python3
"""
EAP3 轻量监控脚本 - 纯API版（适配2核4G）
只检测待办，不自动审批，减少资源占用
"""

import requests
import json
import os
from datetime import datetime

EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    log("=" * 40)
    log("EAP3 轻量监控 (纯API版)")
    log("=" * 40)
    
    try:
        # 登录
        url = f"{EAP3_URL}/r/w"
        post_data = {
            "userid": USER_ID,
            "pwd": ENCRYPTED_PWD,
            "cmd": "com.actionsoft.apps.tengen.login",
            "rememberMeUid": "",
            "rememberMePwd": "",
            "sid": "",
            "token": "",
            "deviceType": "pc",
            "ssoId": "",
            "phone": "",
            "_CACHE_LOGIN_TIME_": str(int(datetime.now().timestamp() * 1000)),
            "redirect_url": "null",
            "lang": "cn",
            "pwdEncode": "RSA",
            "timeZone": "8"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        session = requests.Session()
        resp = session.post(url, data=post_data, headers=headers, timeout=30)
        data = resp.json()
        
        if not data.get("data", {}).get("sid"):
            log("登录失败")
            return
        
        # 获取通知
        params = {
            "sid": data["data"]["sid"],
            "cmd": "com.actionsoft.apps.notification_load_unread_msg"
        }
        resp2 = session.post(f"{EAP3_URL}/r/jd", params=params, headers=headers, timeout=30)
        data2 = resp2.json()
        
        if data2.get("result") != "ok":
            log("获取通知失败")
            return
        
        amount = data2.get("data", {}).get("amount", 0)
        log(f"未读通知: {amount} 条")
        
        # 统计 XZ38 定制需求
        xz38_count = 0
        for item in data2.get("data", {}).get("list", []):
            content = item.get("content", "")
            if "XZ38" in content and ("定制" in content or "新产品需求" in content):
                xz38_count += 1
                user_name = item.get("userName", "")
                log(f"  - {user_name}: {content[:50]}...")
        
        if xz38_count > 0:
            log(f"发现 {xz38_count} 条 XZ38 定制需求待审批")
            # 记录到文件，供后续处理
            notify_file = "/root/.openclaw/logs/eap3_pending_xz38.json"
            with open(notify_file, "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "count": xz38_count,
                    "message": f"发现 {xz38_count} 条 XZ38 定制需求待审批"
                }, f)
        else:
            log("无 XZ38 定制需求")
        
    except Exception as e:
        log(f"异常: {e}")
    
    log("检查完成")

if __name__ == "__main__":
    main()
