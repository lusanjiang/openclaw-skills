#!/usr/bin/env python3
"""
EAP3 审批 - 父窗口打开版
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
    log("EAP3 审批 - 父窗口版")
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
            
            log(f"\n找到 {len(first_page_data)} 条XZ38待办")
            
            for i, todo in enumerate(first_page_data, 1):
                title = todo.get('title', 'Unknown')[:40]
                process_id = todo.get('processInstId')
                
                log(f"\n[{i}/{len(first_page_data)}] {title}")
                
                if not process_id:
                    log("  跳过 - 无processInstId")
                    continue
                
                try:
                    # 在iframe中点击，但通过parent窗口打开
                    result = await frames[1].evaluate(f'''
                        () => {{
                            try {{
                                const rows = document.querySelectorAll('tr');
                                let targetRow = null;
                                let rowIndex = -1;
                                
                                for (let idx = 0; idx < rows.length; idx++) {{
                                    const row = rows[idx];
                                    if (row.innerText.includes('XZ38') && 
                                        (row.innerText.includes('{title[20:30]}') || 
                                         row.innerText.includes('{process_id[:8]}'))) {{
                                        targetRow = row;
                                        rowIndex = idx;
                                        break;
                                    }}
                                }}
                                
                                if (!targetRow) return 'Row not found';
                                
                                // 获取链接的onclick
                                const link = targetRow.querySelector('a');
                                if (!link) return 'No link';
                                
                                const onclick = link.getAttribute('onclick');
                                if (!onclick) {{
                                    // 没有onclick，尝试直接触发
                                    link.click();
                                    return 'Direct click';
                                }}
                                
                                // 解析onclick中的URL
                                const match = onclick.match(/openTask\\(['"]([^'"]+)['"]/);
                                if (match) {{
                                    const taskId = match[1];
                                    // 在parent窗口打开
                                    if (window.parent && window.parent !== window) {{
                                        window.parent.eval(onclick);
                                        return 'Parent eval: ' + onclick.substring(0, 50);
                                    }}
                                    eval(onclick);
                                    return 'Eval: ' + onclick.substring(0, 50);
                                }}
                                
                                // 直接执行onclick
                                eval(onclick);
                                return 'Eval onclick';
                                
                            }} catch(e) {{
                                return 'Error: ' + e.message;
                            }}
                        }}
                    ''')
                    
                    log(f"  结果: {result}")
                    await page.wait_for_timeout(5000)
                    
                    # 检查当前URL是否变化
                    current_url = page.url
                    log(f"  当前URL: {current_url[:60]}...")
                    
                    # 截图
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_step{i}.png", full_page=True)
                    
                except Exception as e:
                    log(f"  ✗ 失败: {e}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
