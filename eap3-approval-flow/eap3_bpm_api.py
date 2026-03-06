#!/usr/bin/env python3
"""
EAP3 审批 - 直接BPM API版
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
    log("EAP3 审批 - BPM API探索版")
    log("=" * 50)
    
    sid = api_login()
    if not sid:
        return
    log(f"✓ SID: {sid[:15]}...")
    
    # 先用requests尝试找到正确的API
    session = requests.Session()
    
    # 可能的API列表
    apis_to_try = [
        # BPM相关
        "com.actionsoft.bpm.engine.web.TodoWeb",
        "com.actionsoft.bpm.engine.web.ProcessWeb", 
        "com.actionsoft.bpm.engine.web.TaskWeb",
        # 工作台相关
        "com.actionsoft.apps.workbench.web.WorkbenchWeb",
        # 通用打开
        "com.actionsoft.bpm.engine.web.PortalWeb",
    ]
    
    for api in apis_to_try:
        try:
            resp = session.post(f"{EAP3_URL}/r/w", data={
                "sid": sid,
                "cmd": api,
                "action": "getTodoList"
            }, timeout=10)
            if resp.status_code == 200 and 'error' not in resp.text.lower():
                log(f"API {api} 可访问")
        except:
            pass
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 访问工作台
            log("\n访问工作台...")
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # 点击待办任务
            log("点击待办任务...")
            try:
                await page.click('text=待办任务', timeout=5000)
                await page.wait_for_timeout(8000)
            except:
                pass
            
            # 监听所有网络请求
            log("\n监听网络请求...")
            
            requests_log = []
            def handle_route(route, request):
                url = request.url
                if 'cmd=' in url or 'action=' in url:
                    requests_log.append(url)
                route.continue_()
            
            await page.route("**/*", handle_route)
            
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
            
            log(f"找到 {len(first_page_data)} 条待办")
            
            # 尝试点击第一条，记录网络请求
            if first_page_data:
                todo = first_page_data[0]
                task_id = todo.get('id')
                
                # 清除之前的日志
                requests_log.clear()
                
                # 在iframe中点击
                result = await frames[1].evaluate('''() => {
                    const rows = document.querySelectorAll('tr');
                    for (let row of rows) {
                        if (row.innerText.includes('XZ38')) {
                            const link = row.querySelector('a');
                            if (link) {
                                link.click();
                                return 'clicked';
                            }
                        }
                    }
                    return 'not found';
                }''')
                
                log(f"点击结果: {result}")
                await page.wait_for_timeout(5000)
                
                # 查看捕获的请求
                log(f"\n捕获的请求 ({len(requests_log)}):")
                for url in requests_log[:5]:
                    log(f"  {url[:80]}...")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
