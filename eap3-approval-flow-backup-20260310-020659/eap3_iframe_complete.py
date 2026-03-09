#!/usr/bin/env python3
"""
EAP3 审批 - 直接iframe内完成
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
    log("EAP3 审批 - iframe内完成版")
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
            
            # 获取firstPageData和审批
            frames = page.frames
            
            # 获取所有待办数据
            first_page_data = await frames[1].evaluate('''() => {
                const data = window.firstPageData || [];
                const flat = [];
                data.forEach(item => {
                    if (Array.isArray(item)) flat.push(...item);
                    else if (typeof item === 'object') flat.push(item);
                });
                return flat.filter(item => item.title && item.title.includes('XZ38'));
            }''')
            
            log(f"\n找到 {len(first_page_data)} 条XZ38待办")
            
            for i, todo in enumerate(first_page_data, 1):
                title = todo.get('title', 'Unknown')[:40]
                process_id = todo.get('processInstId')
                
                log(f"\n[{i}/{len(first_page_data)}] {title}")
                
                if not process_id:
                    log("  跳过 - 无processInstId")
                    continue
                
                try:
                    # 在iframe中直接执行审批操作
                    result = await frames[1].evaluate(f'''
                        async (processId) => {{
                            try {{
                                // 查找当前行
                                const rows = document.querySelectorAll('tr');
                                let targetRow = null;
                                for (let row of rows) {{
                                    if (row.innerText.includes('{process_id[:8]}') || 
                                        row.innerText.includes('{title[:20]}')) {{
                                        targetRow = row;
                                        break;
                                    }}
                                }}
                                
                                if (!targetRow) return 'Row not found';
                                
                                // 获取行的所有信息
                                const link = targetRow.querySelector('a');
                                if (link) {{
                                    // 获取链接的onclick或href
                                    const onclick = link.getAttribute('onclick');
                                    if (onclick) {{
                                        eval(onclick);
                                        return 'Clicked via onclick';
                                    }}
                                    const href = link.getAttribute('href');
                                    if (href) {{
                                        window.location.href = href;
                                        return 'Navigated to: ' + href;
                                    }}
                                    link.click();
                                    return 'Link clicked';
                                }}
                                
                                return 'No link found';
                            }} catch(e) {{
                                return 'Error: ' + e.message;
                            }}
                        }}
                    ''', process_id)
                    
                    log(f"  点击结果: {result}")
                    await page.wait_for_timeout(5000)
                    
                    # 截图
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_step{i}_clicked.png", full_page=True)
                    
                except Exception as e:
                    log(f"  ✗ 失败: {e}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
