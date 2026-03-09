#!/usr/bin/env python3
"""
EAP3 审批 - 使用BPM API打开任务
"""

import asyncio
import json
import requests
from datetime import datetime
from playwright.async_api import async_playwright

EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def api_login():
    try:
        session = requests.Session()
        resp = session.post(
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
            timeout=30
        )
        data = resp.json()
        return data.get("data", {}).get("sid")
    except Exception as e:
        log(f"登录失败: {e}")
        return None

async def main():
    log("=" * 50)
    log("EAP3 审批 - BPM打开任务版")
    log("=" * 50)
    
    sid = api_login()
    if not sid:
        return
    log(f"✓ SID: {sid[:15]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 访问工作台
            log("访问工作台...")
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # 点击待办任务
            log("点击待办任务...")
            try:
                await page.click('text=待办任务', timeout=5000)
                await page.wait_for_timeout(8000)
            except:
                pass
            
            # 获取firstPageData
            frames = page.frames
            first_page_data = await frames[1].evaluate('''() => {
                const data = window.firstPageData || [];
                const flat = [];
                data.forEach(item => {
                    if (Array.isArray(item)) flat.push(...item);
                    else if (typeof item === 'object') flat.push(item);
                });
                return flat.filter(item => item.title && item.title.includes('XZ38'));
            }''')
            
            log(f"\n找到 {len(first_page_data)} 条待办")
            
            # 尝试使用BPM API打开任务
            for i, todo in enumerate(first_page_data, 1):
                title = todo.get('title', 'Unknown')[:40]
                task_id = todo.get('id')
                process_inst_id = todo.get('processInstId')
                
                log(f"\n[{i}/{len(first_page_data)}] {title}")
                log(f"  taskId: {task_id}")
                log(f"  processInstId: {process_inst_id}")
                
                if not task_id:
                    continue
                
                # 尝试多种URL格式
                urls_to_try = [
                    # BPM portal方式
                    f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.bpm.engine.web.PortalWeb&action=openTask&taskInstId={task_id}",
                    # TaskWeb方式
                    f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.bpm.engine.web.TaskWeb&action=open&id={task_id}",
                    # TodoWeb方式  
                    f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.bpm.engine.web.TodoWeb&action=open&taskInstId={task_id}",
                    # ProcessWeb方式
                    f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.bpm.engine.web.ProcessWeb&action=openTask&processInstId={process_inst_id}",
                    # WorkbenchWeb方式
                    f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench.web.WorkbenchWeb&action=openTask&taskInstId={task_id}",
                ]
                
                for url in urls_to_try:
                    try:
                        log(f"  尝试: {url[50:90]}...")
                        await page.goto(url, timeout=30000)
                        await page.wait_for_timeout(5000)
                        
                        # 检查页面内容
                        content = await page.content()
                        
                        if '内部错误' not in content and 'Error' not in content and len(content) > 5000:
                            log(f"  ✓ 可能成功加载")
                            await page.screenshot(path=f"/root/.openclaw/logs/eap3_bpm_{i}.png", full_page=True)
                            
                            # 尝试审批
                            for btn in ['接收办理', '确定', '已核实请后台支持', '提交']:
                                try:
                                    await page.click(f'text={btn}', timeout=2000)
                                    log(f"    ✓ {btn}")
                                    await page.wait_for_timeout(2000)
                                except:
                                    pass
                            break
                        else:
                            log(f"  ✗ 错误页面")
                            
                    except Exception as e:
                        log(f"  ✗ 失败: {e}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
