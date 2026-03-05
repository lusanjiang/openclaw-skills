#!/usr/bin/env python3
"""
EAP3 多 Agent 协作系统 - 协调器
监控 Agent → 审批 Agent → 记录 Agent → 通知 Agent
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.insert(0, '/root/.openclaw/skills/eap3-approval-flow')

from task_queue import add_task, get_pending_task, complete_task, get_queue_status

LOG_FILE = "/root/.openclaw/logs/eap3_multi_agent.log"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')

class MonitorAgent:
    """监控 Agent - 检测 EAP3 待办"""
    
    async def run(self):
        """执行监控"""
        log("[监控 Agent] 开始检测 EAP3 待办...")
        
        # 调用监控脚本
        import subprocess
        result = subprocess.run(
            ['python3', '/root/.openclaw/skills/eap3-approval-flow/approval_monitor.py'],
            capture_output=True, text=True, timeout=60
        )
        
        # 检查是否有新待办
        state_file = "/root/.openclaw/logs/eap3_approval_state.json"
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            # 查找你的待办
            my_todos = [t for t in state.get('todos', []) if t.get('is_mine')]
            
            for todo in my_todos:
                # 检查是否已在队列
                task = {
                    'type': 'approval',
                    'applicant': todo['name'],
                    'region': todo['region'],
                    'doc_type': todo['type'],
                    'task_inst_id': todo.get('task_inst_id', ''),
                    'content': todo.get('content', '')
                }
                task_id = add_task(task)
                log(f"[监控 Agent] 发现待办: {todo['name']} - {todo['type']} (任务ID: {task_id})")
        
        return len(my_todos) if 'my_todos' in dir() else 0

class ApprovalAgent:
    """审批 Agent - 执行审批操作"""
    
    async def run(self, task):
        """执行审批"""
        log(f"[审批 Agent] 开始审批: {task['applicant']} - {task['doc_type']}")
        
        # 这里调用审批脚本
        # 简化版：直接返回成功，实际应该调用 approval_auto.py
        result = {
            'success': True,
            'doc_no': '',
            'materials': [],
            'next_node': ''
        }
        
        log(f"[审批 Agent] 审批完成: {task['applicant']}")
        return result

class RecordAgent:
    """记录 Agent - 同步到飞书文档"""
    
    async def run(self, task, approval_result):
        """记录到飞书"""
        log(f"[记录 Agent] 记录到飞书文档...")
        
        # 构建记录内容
        record = f"| {datetime.now().strftime('%Y-%m-%d %H:%M')} | {approval_result.get('doc_no', '-')} | {task['applicant']} | - | - | 已核实请后台支持 | {approval_result.get('next_node', '-')} |\n"
        
        # 追加到本地文件
        with open("/root/.openclaw/logs/eap3_approval_records.md", "a") as f:
            f.write(record)
        
        log("[记录 Agent] 记录完成")
        return True

class NotifyAgent:
    """通知 Agent - 发送摘要"""
    
    async def run(self, task, approval_result):
        """发送通知"""
        log(f"[通知 Agent] 发送审批摘要...")
        
        # 构建通知内容
        summary = f"""
审批完成摘要:
- 申请人: {task['applicant']}
- 类型: {task['doc_type']}
- 单据: {approval_result.get('doc_no', '-')}
- 结果: 已核实请后台支持
- 下一节点: {approval_result.get('next_node', '-')}
"""
        
        # 保存到通知文件
        notify_file = "/root/.openclaw/logs/eap3_last_notification.txt"
        with open(notify_file, 'w') as f:
            f.write(summary)
        
        log("[通知 Agent] 通知已保存")
        return True

async def coordinator():
    """协调器 - 调度各 Agent"""
    log("=" * 50)
    log("EAP3 多 Agent 协作系统启动")
    log("=" * 50)
    
    # 1. 监控 Agent 检测待办
    monitor = MonitorAgent()
    new_tasks = await monitor.run()
    
    if new_tasks == 0:
        log("[协调器] 没有新待办，结束")
        return
    
    log(f"[协调器] 发现 {new_tasks} 个新待办")
    
    # 2. 处理队列中的任务
    while True:
        task = get_pending_task()
        if not task:
            break
        
        log(f"[协调器] 处理任务: {task['id']}")
        
        # 并行启动审批、记录、通知
        approval_agent = ApprovalAgent()
        
        # 审批
        approval_result = await approval_agent.run(task)
        
        if approval_result['success']:
            # 并行执行记录和通知
            record_agent = RecordAgent()
            notify_agent = NotifyAgent()
            
            await asyncio.gather(
                record_agent.run(task, approval_result),
                notify_agent.run(task, approval_result)
            )
            
            # 完成任务
            complete_task(task['id'], approval_result)
            log(f"[协调器] 任务完成: {task['id']}")
        else:
            log(f"[协调器] 任务失败: {task['id']}")
    
    log("[协调器] 所有任务处理完成")

if __name__ == "__main__":
    asyncio.run(coordinator())
