#!/usr/bin/env python3
"""
EAP3 审批流程自动化脚本
豆爸专用 - 定制需求审批
"""

import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

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

async def login_and_get_todos():
    """登录并获取待办列表"""
    todos = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 登录
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
            
            # 获取待办
            content = await page.content()
            
            # 查找待办
            if '样品试用申请' in content or '定制' in content:
                # 提取人名
                for name in TEAM_FUJIAN + TEAM_JIANGXI:
                    if name in content:
                        region = "福建" if name in TEAM_FUJIAN else "江西"
                        todos.append({"name": name, "region": region})
            
            return browser, context, page, todos
            
        except Exception as e:
            log(f"登录异常: {e}")
            await browser.close()
            return None, None, None, []

async def extract_material_info(page):
    """提取定制物料信息"""
    materials = []
    
    try:
        content = await page.content()
        
        # 匹配物料行
        # 示例: 接触器类.接触器.CJX1 IO_温州工控二车间 无 CJX1-32/2 32A DC36V 0
        pattern = r'(\d+)\s+([^\s]+\.[^\s]+\.[^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\d]+)\s+(\d+)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            materials.append({
                "no": match[0],
                "series": match[1],
                "company": match[2],
                "env": match[3],
                "desc": match[4].strip(),
                "price": match[5]
            })
            
    except Exception as e:
        log(f"提取物料异常: {e}")
    
    return materials

async def approve_with_option(page, option="已核实请后台支持"):
    """执行审批"""
    try:
        # 选择审批选项
        if option == "已核实请后台支持":
            await page.click('radio[value="已核实请后台支持"], input[value="已核实请后台支持"]')
        
        # 点击提交
        await page.click('button:has-text("Submit"), button:has-text("提交")')
        await page.wait_for_timeout(3000)
        
        return True
    except Exception as e:
        log(f"审批异常: {e}")
        return False

async def main():
    """主函数"""
    log("=" * 40)
    log("EAP3 审批流程自动化")
    log("=" * 40)
    
    # 登录并获取待办
    browser, context, page, todos = await login_and_get_todos()
    
    if not todos:
        log("没有待办需要处理")
        if browser:
            await browser.close()
        return
    
    log(f"发现 {len(todos)} 条待办")
    
    # 处理第一个待办
    todo = todos[0]
    log(f"处理: {todo['name']} - {todo['region']}")
    
    # 提取物料信息
    materials = await extract_material_info(page)
    
    if materials:
        log("📦 定制物料信息:")
        for m in materials:
            log(f"  - {m['series']}")
            log(f"    生产: {m['company']}")
            log(f"    描述: {m['desc']}")
            log(f"    价格: {m['price']}")
    
    # 等待用户确认（实际使用时通过消息交互）
    log("等待用户确认...")
    
    # 关闭浏览器
    if browser:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
