#!/usr/bin/env python3
"""
EAP3 多 Agent 协作系统 - 任务队列管理
豆爸专用
"""

import json
import os
from datetime import datetime
from pathlib import Path

QUEUE_FILE = "/root/.openclaw/logs/eap3_task_queue.json"
RESULT_FILE = "/root/.openclaw/logs/eap3_task_results.json"

def init_queue():
    """初始化队列文件"""
    Path(QUEUE_FILE).parent.mkdir(parents=True, exist_ok=True)
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'w') as f:
            json.dump({"pending": [], "processing": [], "completed": []}, f)

def add_task(task):
    """添加任务到队列"""
    init_queue()
    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)
    
    task['id'] = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task['status'] = 'pending'
    task['created_at'] = datetime.now().isoformat()
    
    queue['pending'].append(task)
    
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)
    
    return task['id']

def get_pending_task():
    """获取一个待处理任务"""
    init_queue()
    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)
    
    if queue['pending']:
        task = queue['pending'].pop(0)
        task['status'] = 'processing'
        task['started_at'] = datetime.now().isoformat()
        queue['processing'].append(task)
        
        with open(QUEUE_FILE, 'w') as f:
            json.dump(queue, f, indent=2)
        
        return task
    return None

def complete_task(task_id, result):
    """完成任务"""
    init_queue()
    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)
    
    # 从 processing 移到 completed
    for task in queue['processing']:
        if task['id'] == task_id:
            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            task['result'] = result
            queue['processing'].remove(task)
            queue['completed'].append(task)
            break
    
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)

def get_queue_status():
    """获取队列状态"""
    init_queue()
    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)
    
    return {
        "pending": len(queue['pending']),
        "processing": len(queue['processing']),
        "completed": len(queue['completed'])
    }

if __name__ == "__main__":
    print("队列管理模块")
    print(f"队列状态: {get_queue_status()}")
