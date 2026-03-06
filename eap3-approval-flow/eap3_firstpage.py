#!/usr/bin/env python3
"""
EAP3 审批 - 使用firstPageData
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
    log("EAP3 审批 - firstPageData版")
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
            
            # 从Frame 1获取firstPageData
            frames = page.frames
            log(f"页面有 {len(frames)} 个frame")
            
            # 获取firstPageData
            first_page_data = await frames[1].evaluate('() => window.firstPageData || []')
            
            # firstPageData是嵌套列表，需要展平
            flat_data = []
            for item in first_page_data:
                if isinstance(item, list):
                    flat_data.extend(item)
                elif isinstance(item, dict):
                    flat_data.append(item)
            
            # 过滤XZ38待办
            todos = []
            for item in flat_data:
                if isinstance(item, dict):
                    title = item.get('title', '')
                    if 'XZ38' in title and '定制' in title:
                        todos.append(item)
            
            log(f"\n找到 {len(todos)} 条XZ38待办")
            for i, todo in enumerate(todos, 1):
                log(f"[{i}] {todo.get('title', '')[:50]}...")
                log(f"    taskInstId: {todo.get('taskInstId', 'N/A')}")
                log(f"    processInstId: {todo.get('processInstId', 'N/A')}")
            
            if not todos:
                log("无待办")
                return
            
            # 逐条审批
            for i, todo in enumerate(todos, 1):
                task_inst_id = todo.get('taskInstId')
                process_inst_id = todo.get('processInstId')
                title = todo.get('title', 'Unknown')[:30]
                
                if not process_inst_id:
                    log(f"\n[{i}] 跳过 - 无processInstId")
                    continue
                
                log(f"\n[{i}/{len(todos)}] {title}")
                
                try:
                    # 构造打开URL - 使用processInstId
                    open_url = f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_open_process_inst&processInstId={process_inst_id}"
                    log(f"  打开: {open_url[:70]}...")
                    
                    await page.goto(open_url, timeout=60000)
                    await page.wait_for_timeout(10000)
                    
                    # 截图
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_{task_inst_id}.png", full_page=True)
                    
                    # 审批步骤
                    actions = [
                        ('接收办理', 3),
                        ('确定', 3),
                        ('已核实请后台支持', 2),
                        ('提交', 5)
                    ]
                    
                    for btn_text, wait_sec in actions:
                        try:
                            await page.click(f'text={btn_text}', timeout=5000)
                            log(f"  ✓ {btn_text}")
                            await page.wait_for_timeout(wait_sec * 1000)
                        except:
                            # 尝试替代文本
                            alts = {'接收办理': ['办理', '接收'], '确定': ['确认'], '提交': ['发送']}
                            found = False
                            for alt in alts.get(btn_text, []):
                                try:
                                    await page.click(f'text={alt}', timeout=2000)
                                    log(f"  ✓ {alt}")
                                    await page.wait_for_timeout(wait_sec * 1000)
                                    found = True
                                    break
                                except:
                                    pass
                            if not found:
                                log(f"  - {btn_text} (未找到)")
                    
                    log(f"✓ 完成")
                    
                except Exception as e:
                    log(f"✗ 失败: {e}")
            
            log("\n审批执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
