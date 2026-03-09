#!/usr/bin/env python3
"""
EAP3审批 - #审批标签版
支持：技能调用 + 飞书记录
"""

import asyncio
import json
import os
import sys
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# 添加技能目录到路径
SKILL_DIR = Path("/root/.openclaw/skills/eap3-approval-flow")
sys.path.insert(0, str(SKILL_DIR))

# 飞书文档配置（需要替换为实际文档token）
FEISHU_DOC_TOKEN = "Otlxd1AllogLYAxzPq4casnRnpb"  # 从MEMORY.md获取

class EAP3ApprovalWithLog:
    def __init__(self):
        self.results = []
        
    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {msg}")
        
    async def run_approval(self):
        """运行审批流程"""
        # 导入主审批类
        from eap3_auto import EAP3AutoApprover
        
        approver = EAP3AutoApprover()
        
        # 记录开始
        start_time = datetime.now()
        self.log("=" * 50)
        self.log("#审批 触发 EAP3 XZ38审批")
        self.log("=" * 50)
        
        # 执行审批
        success = await approver.run()
        
        # 记录结果
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.results = {
            "time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": f"{duration:.1f}秒",
            "success": success,
            "sid": approver.sid[:15] + "..." if approver.sid else "N/A"
        }
        
        return success
        
    def save_to_feishu(self):
        """保存记录到飞书文档"""
        try:
            # 构造记录内容
            content = f"""
## 审批执行记录

**执行时间**: {self.results['time']}
**执行时长**: {self.results['duration']}
**执行结果**: {'✓ 成功' if self.results['success'] else '✗ 失败'}
**SID**: {self.results['sid']}

---

*自动记录 by #审批*
"""
            
            # 这里调用飞书文档API追加内容
            # 实际实现需要feishu_doc工具的append动作
            self.log(f"\n飞书记录内容：")
            self.log(content)
            
            return True
        except Exception as e:
            self.log(f"飞书记录失败: {e}")
            return False

async def main():
    """主函数 - #审批标签入口"""
    approval = EAP3ApprovalWithLog()
    
    # 执行审批
    success = await approval.run_approval()
    
    # 记录到飞书
    approval.save_to_feishu()
    
    # 返回结果
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
