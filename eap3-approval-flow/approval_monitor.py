#!/usr/bin/env python3
"""
EAP3 审批流程监控脚本 - 监控版
每20分钟检查一次，发现待办时发送飞书通知
豆爸专用
"""

import requests
import json
import os
import re
from datetime import datetime

# 配置
EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

# 销售团队名单
TEAM_FUJIAN = ["茅智伟", "谢品", "林志伟", "吴国强", "黄丽萍", "何超阳", "唐悠梅"]
TEAM_JIANGXI = ["肖培坤", "程明锦", "李志辉", "江伟康", "熊澄伟", "刘荣德", "胡洪箭", "朱海平", "陈毅"]

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def login():
    """登录获取SID"""
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
    
    try:
        session = requests.Session()
        resp = session.post(url, data=post_data, headers=headers, timeout=30)
        data = resp.json()
        
        if data.get("data", {}).get("sid"):
            return data["data"]["sid"]
        else:
            return None
    except Exception as e:
        log(f"登录异常: {e}")
        return None

def get_notifications(sid):
    """获取未读通知/待办"""
    url = f"{EAP3_URL}/r/jd"
    
    params = {
        "sid": sid,
        "cmd": "com.actionsoft.apps.notification_load_unread_msg"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{EAP3_URL}/r/w"
    }
    
    try:
        resp = requests.post(url, params=params, headers=headers, timeout=30)
        data = resp.json()
        
        if data.get("result") == "ok":
            amount = data.get("data", {}).get("amount", 0)
            notify_list = data.get("data", {}).get("list", [])
            return amount, notify_list
        else:
            return 0, []
    except Exception as e:
        log(f"获取通知异常: {e}")
        return 0, []

def parse_todos(notify_list):
    """解析通知列表，提取待办信息"""
    todos = []
    
    for item in notify_list:
        content = item.get("content", "")
        user_name = item.get("userName", "")
        dept = item.get("departmentName", "")
        task_inst_id = item.get("sourceId", "")
        
        # 判断类型
        todo_type = "其他"
        if "定制" in content or "新产品需求" in content:
            todo_type = "定制及新产品需求"
        elif "样品试用" in content:
            todo_type = "样品试用申请"
        
        # 判断所属区域
        region = "其他"
        if user_name in TEAM_FUJIAN:
            region = "福建"
        elif user_name in TEAM_JIANGXI:
            region = "江西"
        
        todos.append({
            "name": user_name,
            "department": dept,
            "type": todo_type,
            "content": content[:100],
            "region": region,
            "is_mine": True,  # 全体审批，不限制区域
            "task_inst_id": task_inst_id
        })
    
    return todos

def load_last_state():
    """加载上次状态"""
    state_file = "/root/.openclaw/logs/eap3_approval_state.json"
    if not os.path.exists(state_file):
        return {"count": 0, "todos": []}
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"count": 0, "todos": []}

def save_state(count, todos):
    """保存当前状态"""
    state_file = "/root/.openclaw/logs/eap3_approval_state.json"
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    
    state = {
        "last_check": datetime.now().isoformat(),
        "count": count,
        "todos": todos
    }
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def send_feishu_notification(todo):
    """发送飞书通知（通过OpenClaw message工具）"""
    # 构建通知消息
    message = f"""🔔 EAP3 待办提醒 - 需要审批

【{todo['region']}】{todo['name']} - {todo['type']}
部门：{todo['department']}

回复 "#审批流程" 开始自动处理
或登录 EAP3 查看详情"""
    
    # 写入通知文件，供外部读取
    notify_file = "/root/.openclaw/logs/eap3_pending_approval.json"
    with open(notify_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "todo": todo,
            "message": message
        }, f, ensure_ascii=False, indent=2)
    
    log(f"待办已记录: {todo['name']}")
    log(f"  类型: {todo['type']}")
    log(f"  消息已保存到: {notify_file}")

def main():
    """主函数"""
    log("=" * 40)
    log("EAP3 审批流程监控")
    log("=" * 40)
    
    # 登录获取SID
    sid = login()
    if not sid:
        log("登录失败，退出")
        return
    
    # 获取通知/待办
    count, notify_list = get_notifications(sid)
    log(f"未读通知数量: {count}")
    
    # 解析待办
    todos = parse_todos(notify_list)
    
    # 分类统计
    my_todos = [t for t in todos if t["is_mine"]]
    
    if my_todos:
        log(f"发现 {len(my_todos)} 条你的待办:")
        for t in my_todos:
            log(f"  - [{t['region']}] {t['name']}: {t['type']}")
    
    # 加载上次状态
    last_state = load_last_state()
    last_count = last_state.get("count", 0)
    last_todos = last_state.get("todos", [])
    
    # 找出新待办
    last_ids = set(td.get("task_inst_id", "") for td in last_todos)
    new_todos = [t for t in my_todos if t.get("task_inst_id", "") not in last_ids]
    
    # 发送新待办通知
    for todo in new_todos:
        send_feishu_notification(todo)
    
    # 判断数量变化
    if count > last_count:
        log(f"⚠️ 待办增加: {last_count} -> {count}")
    elif count < last_count:
        log(f"✓ 待办减少: {last_count} -> {count}")
    else:
        log("数量无变化")
    
    # 保存状态
    save_state(count, todos)
    log("检查完成")

if __name__ == "__main__":
    main()
