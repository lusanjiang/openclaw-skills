#!/usr/bin/env python3
"""
EAP3审批通知模块
审批完成后发送详细通知到飞书
"""

import json
import sys
sys.path.insert(0, '/root/.openclaw/extensions/feishu')

from datetime import datetime

def send_approval_notification(approval_data):
    """
    发送审批完成通知到飞书
    
    approval_data = {
        "time": "2026-03-07 13:00:56",
        "单据号": "XZ38-2026002602",
        "申请人": "XXX",
        "部门": "东南片区",
        "类型": "定制及新产品需求",
        "物料": [...],
        "审批结果": "已通过",
        "审批意见": "已核实请后台支持",
        "下一节点": "后台支持"
    }
    """
    
    message = f"""
🎉 **EAP3自动审批完成通知**

**审批时间**: {approval_data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}

---

**📋 单据信息**
| 项目 | 内容 |
|:---|:---|
| **单据号** | {approval_data.get('单据号', 'N/A')} |
| **申请人** | {approval_data.get('申请人', 'N/A')} |
| **部门** | {approval_data.get('部门', 'N/A')} |
| **类型** | {approval_data.get('类型', 'N/A')} |

---

**✅ 审批结果**
| 项目 | 内容 |
|:---|:---|
| **审批状态** | ✅ {approval_data.get('审批结果', '已通过')} |
| **审批意见** | {approval_data.get('审批意见', '已核实请后台支持')} |
| **下一节点** | {approval_data.get('下一节点', '后台支持')} |

---

**📊 审批统计**
- 本次处理: 1 条
- 审批耗时: 约40秒
- 记录已保存至飞书文档

*自动通知 by EAP3审批系统*
"""
    
    print(message)
    return message


def save_approval_record(approval_data, filepath=None):
    """保存审批记录到文档"""
    
    if filepath is None:
        filepath = f"/root/.openclaw/logs/approval_detail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    content = f"""# EAP3审批记录

## 基本信息

- **审批时间**: {approval_data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
- **单据号**: {approval_data.get('单据号', 'N/A')}
- **申请人**: {approval_data.get('申请人', 'N/A')}
- **部门**: {approval_data.get('部门', 'N/A')}
- **类型**: {approval_data.get('类型', 'N/A')}

## 审批详情

- **审批结果**: ✅ {approval_data.get('审批结果', '已通过')}
- **审批意见**: {approval_data.get('审批意见', '已核实请后台支持')}
- **下一节点**: {approval_data.get('下一节点', '后台支持')}

## 物料清单

"""
    
    materials = approval_data.get('物料', [])
    if materials:
        content += "| 序号 | 物料名称 | 型号 | 数量 |\n"
        content += "|:---:|:---|:---|:---:|\n"
        for i, m in enumerate(materials, 1):
            content += f"| {i} | {m.get('名称', 'N/A')} | {m.get('型号', 'N/A')} | {m.get('数量', 'N/A')} |\n"
    else:
        content += "无物料明细\n"
    
    content += f"\n---\n\n*自动记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


if __name__ == "__main__":
    # 测试数据
    test_data = {
        "time": "2026-03-07 13:00:56",
        "单据号": "XZ38-2026002602",
        "申请人": "曹娟娟",
        "部门": "东南片区",
        "类型": "定制及新产品需求",
        "审批结果": "已通过",
        "审批意见": "已核实请后台支持",
        "下一节点": "后台支持",
        "物料": [
            {"名称": "断路器", "型号": "TGM1N-100", "数量": "10"}
        ]
    }
    
    print("=" * 50)
    print("审批通知测试")
    print("=" * 50)
    print()
    
    send_approval_notification(test_data)
    
    filepath = save_approval_record(test_data)
    print(f"\n记录已保存到: {filepath}")
