#!/usr/bin/env python3
"""
EAP3 审批 - 直接提取打开函数
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
    log("EAP3 审批 - 提取打开函数")
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
            
            # 获取完整的页面内容
            html = await frames[1].content()
            
            # 查找所有的script内容
            log("\n查找内联脚本...")
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
            
            for i, script in enumerate(scripts):
                if 'open' in script or 'click' in script or 'task' in script.lower():
                    log(f"\n脚本 {i} (长度: {len(script)}):")
                    # 查找函数定义
                    funcs = re.findall(r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*(?:open|task|todo)', script, re.IGNORECASE | re.DOTALL)
                    if funcs:
                        log(f"  找到函数: {funcs}")
                    
                    # 查找包含特定模式的代码
                    if 'openTodo' in script or 'openTask' in script:
                        log(f"  内容: {script[:500]}")
            
            # 直接尝试调用可能存在的函数
            log("\n尝试调用可能的打开函数...")
            
            # 获取第一条待办的ID
            first_page_data = await frames[1].evaluate('''() => {
                const data = window.firstPageData || [];
                const flat = [];
                data.forEach(item => {
                    if (Array.isArray(item)) flat.push(...item);
                    else if (typeof item === 'object') flat.push(item);
                });
                return flat.filter(item => item.title && item.title.includes('XZ38'));
            }''')
            
            if first_page_data:
                task_id = first_page_data[0].get('id')
                log(f"使用taskId: {task_id}")
                
                # 尝试各种可能的调用方式
                results = await frames[1].evaluate(f'''
                    (taskId) => {{
                        const results = {{}};
                        
                        // 尝试1: 直接函数调用
                        if (typeof openTodo === 'function') {{
                            try {{ openTodo(taskId); results.openTodo = 'called'; }} catch(e) {{ results.openTodo = e.message; }}
                        }}
                        if (typeof openTask === 'function') {{
                            try {{ openTask(taskId); results.openTask = 'called'; }} catch(e) {{ results.openTask = e.message; }}
                        }}
                        
                        // 尝试2: 从link的ID构造
                        const link = document.getElementById('a-' + taskId);
                        if (link) {{
                            results.linkFound = true;
                            
                            // 尝试直接触发link的点击事件
                            const event = new MouseEvent('click', {{ bubbles: true }});
                            link.dispatchEvent(event);
                            results.eventDispatched = true;
                            
                            // 尝试使用jQuery
                            if (typeof jQuery !== 'undefined') {{
                                jQuery(link).trigger('click');
                                results.jQueryTriggered = true;
                            }}
                        }}
                        
                        return results;
                    }}
                ''', task_id)
                
                log(f"调用结果: {json.dumps(results, ensure_ascii=False)}")
                
                await page.wait_for_timeout(3000)
                
                # 检查URL
                current_url = page.url
                log(f"当前URL: {current_url[:80]}...")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
