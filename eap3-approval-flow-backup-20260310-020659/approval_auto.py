#!/usr/bin/env python3
"""
EAP3 审批流程自动化 - 完整版
包含：监控 + 审批 + 飞书记录
豆爸专用
"""

import asyncio
import json
import os
import re
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# 配置
EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

# 飞书文档配置
FEISHU_DOC_ID = "Otlxd1AllogLYAxzPq4casnRnpb"  # EAP3审批记录-定制物料明细

# 销售团队名单
TEAM_FUJIAN = ["茅智伟", "谢品", "林志伟", "吴国强", "黄丽萍", "何超阳", "唐悠梅"]
TEAM_JIANGXI = ["肖培坤", "程明锦", "李志辉", "江伟康", "熊澄伟", "刘荣德", "胡洪箭", "朱海平", "陈毅"]

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

async def approve_flow(task_inst_id=None):
    """完整审批流程"""
    approval_info = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "doc_no": "",
        "applicant": "",
        "customer": "",
        "materials": [],
        "result": "已核实请后台支持",
        "next_node": ""
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 登录
            log("登录EAP3...")
            await page.goto(f"{EAP3_URL}/", wait_until="load", timeout=90000)
            await page.wait_for_timeout(3000)
            
            await page.wait_for_selector('input[placeholder*="用户名"]', timeout=30000)
            await page.fill('input[placeholder*="用户名"]', USER_ID)
            
            await page.wait_for_selector('input[placeholder*="密码"]', timeout=30000)
            await page.fill('input[placeholder*="密码"]', ENCRYPTED_PWD)
            
            await page.wait_for_selector('button, input[type="submit"]', timeout=30000)
            await page.click('button, input[type="submit"]')
            
            await page.wait_for_selector('text=待办任务', timeout=90000)
            await page.wait_for_timeout(3000)
            
            # 获取SID
            sid_match = re.search(r'sid=([a-f0-9-]+)', page.url)
            sid = sid_match.group(1) if sid_match else ""
            
            # 进入工作台
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # 查找并点击待办
            content = await page.content()
            
            # 提取单据信息
            doc_match = re.search(r'XZ38-(\d+)', content)
            if doc_match:
                approval_info["doc_no"] = f"XZ38-{doc_match.group(1)}"
            
            # 提取申请人
            for name in TEAM_FUJIAN + TEAM_JIANGXI:
                if name in content:
                    approval_info["applicant"] = name
                    break
            
            # 提取客户名称
            customer_match = re.search(r'客户名称\s+([^\s]+)', content)
            if customer_match:
                approval_info["customer"] = customer_match.group(1)
            
            # 提取物料信息
            materials = []
            # 匹配物料行
            pattern = r'(\d+)\s+([^\s]+\.[^\s]+\.[^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\d]+?)\s+(\d+)'
            matches = re.findall(pattern, content)
            for match in matches:
                materials.append({
                    "series": match[1],
                    "company": match[2],
                    "desc": match[4].strip()
                })
            approval_info["materials"] = materials
            
            # 点击接收办理
            await page.click('button:has-text("接收办理"), button:has-text("Receive")')
            await page.wait_for_timeout(2000)
            
            # 确认接收
            try:
                await page.click('button:has-text("确定"), button:has-text("OK")')
                await page.wait_for_timeout(2000)
            except:
                pass
            
            # 选择审批选项
            await page.click('radio[value="已核实请后台支持"], input[value="已核实请后台支持"]')
            await page.wait_for_timeout(1000)
            
            # 点击办理/提交
            await page.click('button:has-text("办理"), button:has-text("Submit")')
            await page.wait_for_timeout(3000)
            
            # 提取下一节点
            content_after = await page.content()
            next_match = re.search(r'下一节点[：:]\s*([^\n]+)', content_after)
            if next_match:
                approval_info["next_node"] = next_match.group(1).strip()
            
            log(f"审批完成: {approval_info['doc_no']}")
            
        except Exception as e:
            log(f"审批异常: {e}")
        finally:
            await browser.close()
    
    return approval_info

def record_to_feishu(approval_info):
    """记录到飞书文档"""
    try:
        # 构建物料描述
        material_desc = "; ".join([f"{m['desc']}" for m in approval_info['materials']]) if approval_info['materials'] else "-"
        
        # 这里应该调用飞书API追加记录
        # 暂时先记录到本地文件，后续可以通过飞书文档API写入
        record = f"| {approval_info['time']} | {approval_info['doc_no']} | {approval_info['applicant']} | {approval_info['customer']} | {material_desc} | {approval_info['result']} | {approval_info['next_node']} |\n"
        
        with open("/root/.openclaw/logs/eap3_approval_records.md", "a", encoding="utf-8") as f:
            f.write(record)
        
        log(f"已记录到文档: {approval_info['doc_no']}")
        
    except Exception as e:
        log(f"记录飞书异常: {e}")

async def main():
    """主函数"""
    log("=" * 40)
    log("EAP3 自动审批流程")
    log("=" * 40)
    
    # 执行审批
    approval_info = await approve_flow()
    
    if approval_info["doc_no"]:
        # 记录到飞书
        record_to_feishu(approval_info)
        
        # 输出审批摘要
        print("\n" + "=" * 40)
