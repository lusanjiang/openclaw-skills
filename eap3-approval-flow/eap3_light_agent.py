#!/usr/bin/env python3
"""
EAP3 单进程轻量版 v3.0
合并: Monitor + Approval + Record + Notify
资源占用: 单进程, 低内存, 适配2核4G

流程:
1. 监控API获取待办
2. 浏览器自动化审批(如需)
3. 记录结果到飞书文档
4. 发送通知
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta

# 配置
EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"
CACHE_DIR = "/root/.openclaw/cache"
LOG_DIR = "/root/.openclaw/logs"
FEISHU_DOC_ID = "Otlxd1AllogLYAxzPq4casnRnpb"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

class EAP3LightAgent:
    def __init__(self):
        self.session = None
        self.sid = None
        self.log_file = f"{LOG_DIR}/eap3_light_{datetime.now().strftime('%Y%m%d')}.log"
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}"
        print(log_line)
        with open(self.log_file, "a") as f:
            f.write(log_line + "\n")
    
    def get_cached_sid(self):
        """获取缓存的SID"""
        cache_file = f"{CACHE_DIR}/eap3_sid.json"
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                cached_time = datetime.fromisoformat(cache.get('timestamp', ''))
                if datetime.now() - cached_time < timedelta(minutes=25):
                    return cache.get('sid')
        except Exception:
            pass
        return None
    
    def save_sid(self, sid):
        """保存SID到缓存"""
        cache_file = f"{CACHE_DIR}/eap3_sid.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({'sid': sid, 'timestamp': datetime.now().isoformat()}, f)
        except Exception as e:
            self.log(f"缓存SID失败: {e}", "WARN")
    
    def login(self):
        """步骤1: 登录获取SID"""
        self.log("=" * 40)
        self.log("[1/4] 登录EAP3...")
        
        # 尝试缓存
        cached_sid = self.get_cached_sid()
        if cached_sid:
            self.sid = cached_sid
            self.session = requests.Session()
            # 验证SID
            try:
                resp = self.session.post(
                    f"{EAP3_URL}/r/jd",
                    params={"sid": self.sid, "cmd": "com.actionsoft.apps.notification_load_unread_msg"},
                    timeout=10
                )
                if resp.json().get("result") == "ok":
                    self.log("使用缓存SID")
                    return True
            except:
                pass
        
        # 重新登录
        self.session = requests.Session()
        try:
            resp = self.session.post(
                f"{EAP3_URL}/r/w",
                data={
                    "userid": USER_ID,
                    "pwd": ENCRYPTED_PWD,
                    "cmd": "com.actionsoft.apps.tengen.login",
                    "deviceType": "pc",
                    "lang": "cn",
                    "pwdEncode": "RSA",
                    "timeZone": "8",
                    "_CACHE_LOGIN_TIME_": str(int(datetime.now().timestamp() * 1000))
                },
                timeout=15
            )
            data = resp.json()
            self.sid = data.get("data", {}).get("sid")
            if self.sid:
                self.save_sid(self.sid)
                self.log("登录成功")
                return True
        except Exception as e:
            self.log(f"登录失败: {e}", "ERROR")
        return False
    
    def check_todos(self):
        """步骤2: 检查待办"""
        self.log("[2/4] 检查待办...")
        try:
            resp = self.session.post(
                f"{EAP3_URL}/r/jd",
                params={"sid": self.sid, "cmd": "com.actionsoft.apps.notification_load_unread_msg"},
                timeout=15
            )
            data = resp.json()
            if data.get("result") != "ok":
                return []
            
            xz38_list = []
            for item in data.get("data", {}).get("list", []):
                content = item.get("content", "")
                if "XZ38" in content and ("定制" in content or "新产品需求" in content):
                    xz38_list.append({
                        "user": item.get("userName", ""),
                        "content": content[:80],
                        "time": datetime.now().isoformat()
                    })
            
            self.log(f"发现 {len(xz38_list)} 条XZ38待办")
            return xz38_list
        except Exception as e:
            self.log(f"检查失败: {e}", "ERROR")
            return []
    
    def approve_todo(self, todo):
        """步骤3: 审批待办(简化版，纯API不可行时标记为手动处理)"""
        self.log(f"[3/4] 审批 {todo['user']}...")
        
        # 当前纯API审批未开放，标记为需要手动处理
        # 后续可接入Playwright浏览器自动化
        result = {
            "user": todo['user'],
            "status": "pending_manual",  # 待手动处理
            "content": todo['content'],
            "time": datetime.now().isoformat(),
            "note": "纯API审批接口未开放，需手动处理或配置浏览器自动化"
        }
        self.log(f"  → 标记为待手动处理")
        return result
    
    def record_to_feishu(self, results):
        """步骤4: 记录到飞书(简化版，写入本地文件)"""
        self.log("[4/4] 记录结果...")
        
        record_file = f"{LOG_DIR}/eap3_approval_records.json"
        try:
            # 读取现有记录
            existing = []
            if os.path.exists(record_file):
                with open(record_file, 'r') as f:
                    existing = json.load(f)
            
            # 添加新记录
            for result in results:
                existing.append(result)
            
            # 保存
            with open(record_file, 'w') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            
            self.log(f"  → 已记录 {len(results)} 条")
        except Exception as e:
            self.log(f"记录失败: {e}", "ERROR")
    
    def notify(self, results):
        """通知(简化版，仅日志)"""
        if results:
            self.log(f"通知: {len(results)} 条待办需处理")
        else:
            self.log("通知: 无待办")
    
    def run(self):
        """主流程"""
        self.log("=" * 40)
        self.log("EAP3 单进程轻量版 v3.0")
        self.log("=" * 40)
        
        start_time = time.time()
        
        # 1. 登录
        if not self.login():
            self.log("流程终止: 登录失败", "ERROR")
            return False
        
        # 2. 检查待办
        todos = self.check_todos()
        if not todos:
            self.log("流程结束: 无待办")
            return True
        
        # 3. 审批
        results = []
        for todo in todos:
            result = self.approve_todo(todo)
            results.append(result)
        
        # 4. 记录
        self.record_to_feishu(results)
        
        # 5. 通知
        self.notify(results)
        
        elapsed = time.time() - start_time
        self.log(f"流程完成，耗时 {elapsed:.1f}s")
        self.log("=" * 40)
        return True

if __name__ == "__main__":
    agent = EAP3LightAgent()
    success = agent.run()
    sys.exit(0 if success else 1)
