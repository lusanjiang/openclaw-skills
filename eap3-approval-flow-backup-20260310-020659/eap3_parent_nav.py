#!/usr/bin/env python3
"""
EAP3 审批 - 父窗口导航版
"""

import asyncio
import json
import re
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
    log("EAP3 审批 - 父窗口导航版")
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
            
            frames = page.frames
            
            # 获取firstPageData
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
            
            for i, todo in enumerate(first_page_data, 1):
                task_id = todo.get('id')
                title = todo.get('title', 'Unknown')[:40]
                
                log(f"\n[{i}/{len(first_page_data)}] {title}")
                log(f"  taskId: {task_id}")
                
                # 每次重新获取frames（因为导航会刷新页面）
                frames = page.frames
                
                # 尝试各种方式在父窗口打开
                try:
                    result = await frames[1].evaluate(f'''
                        (taskId) => {{
                            try {{
                                if (window.parent && window.parent !== window) {{
                                    const sidMatch = window.location.href.match(/sid=([^&]+)/);
                                    const sid = sidMatch ? sidMatch[1] : '';
                                    const url = '/r/w?sid=' + sid + '&cmd=com.actionsoft.apps.workbench&action=openTaskInst&id=' + taskId;
                                    window.parent.location.href = url;
                                    return 'parent.location changed';
                                }}
                                return 'No parent';
                            }} catch(e) {{
                                return 'Error: ' + e.message;
                            }}
                        }}
                    ''', task_id)
                    
                    log(f"  结果: {result}")
                except Exception as e:
                    log(f"  导航错误(可能成功): {e}")
                await page.wait_for_timeout(8000)
                
                # 检查URL
                current_url = page.url
                log(f"  当前URL: {current_url[:80]}...")
                
                # 截图
                await page.screenshot(path=f"/root/.openclaw/logs/eap3_nav_{i}.png", full_page=True)
                
                # 如果在详情页，尝试审批
                if 'workbench' not in current_url or 'open' in current_url or 'process' in current_url:
                    log("  可能在详情页，尝试审批...")
                    for btn in ['接收办理', '确定', '已核实请后台支持', '提交']:
                        try:
                            await page.click(f'text={btn}', timeout=3000)
                            log(f"    ✓ {btn}")
                            await page.wait_for_timeout(3000)
                        except:
                            pass
                
                # 返回工作台处理下一条
                if i < len(first_page_data):
                    log("  返回工作台...")
                    await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
                    await page.wait_for_timeout(5000)
                    try:
                        await page.click('text=待办任务', timeout=3000)
                        await page.wait_for_timeout(5000)
                    except:
                        pass
                    
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
