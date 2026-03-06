#!/usr/bin/env python3
"""
EAP3 审批 - 查找事件委托代码
"""

import asyncio
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
    log("EAP3 审批 - 查找事件委托代码")
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
            
            # 获取所有script内容
            log("\n获取所有脚本...")
            all_scripts = await frames[1].evaluate('''() => {
                const scripts = document.querySelectorAll('script[src]');
                return Array.from(scripts).map(s => s.src).filter(src => src);
            }''')
            
            log(f"找到 {len(all_scripts)} 个外部脚本")
            for src in all_scripts[:5]:
                log(f"  {src}")
            
            # 查找jQuery事件绑定
            log("\n查找jQuery事件绑定...")
            events = await frames[1].evaluate('''() => {
                if (typeof jQuery === 'undefined') return 'jQuery not found';
                
                // 获取所有绑定了click事件的元素
                const allElements = document.querySelectorAll('*');
                const results = [];
                
                for (let el of allElements) {
                    const events = jQuery._data(el, 'events');
                    if (events && events.click) {
                        results.push({
                            tag: el.tagName,
                            id: el.id,
                            class: el.className,
                            handlerCount: events.click.length
                        });
                    }
                }
                
                return results.slice(0, 10);
            }''')
            
            log(f"事件绑定: {events}")
            
            # 查找是否有全局的openTask函数
            log("\n查找全局函数...")
            global_funcs = await frames[1].evaluate('''() => {
                const funcs = [];
                for (let key in window) {
                    if (typeof window[key] === 'function' && 
                        (key.includes('open') || key.includes('task') || key.includes('todo'))) {
                        funcs.push(key);
                    }
                }
                return funcs.slice(0, 20);
            }''')
            
            log(f"相关全局函数: {global_funcs}")
            
            # 尝试找到AWSUI的函数
            log("\n查找AWSUI...")
            awsui = await frames[1].evaluate('''() => {
                if (typeof AWSUI === 'undefined') return 'AWSUI not found';
                return Object.keys(AWSUI).filter(k => typeof AWSUI[k] === 'function').slice(0, 10);
            }''')
            
            log(f"AWSUI函数: {awsui}")
            
            # 尝试找到并调用打开任务的函数
            log("\n尝试调用打开函数...")
            result = await frames[1].evaluate('''() => {
                // 尝试常见的打开函数
                const funcs = ['openTask', 'openTodo', 'openProcess', 'openDetail'];
                for (let func of funcs) {
                    if (typeof window[func] === 'function') {
                        return { found: func, type: 'window' };
                    }
                    if (typeof AWSUI !== 'undefined' && typeof AWSUI[func] === 'function') {
                        return { found: func, type: 'AWSUI' };
                    }
                }
                return 'No open function found';
            }''')
            
            log(f"结果: {result}")
            
            # 尝试使用jQuery触发点击
            log("\n尝试jQuery触发点击...")
            click_result = await frames[1].evaluate('''() => {
                try {
                    if (typeof jQuery === 'undefined') return 'No jQuery';
                    
                    // 找到第一个XZ38的链接
                    const link = document.querySelector('a[id^="a-da3"]');
                    if (!link) return 'Link not found';
                    
                    // 使用jQuery触发点击
                    jQuery(link).trigger('click');
                    return 'jQuery click triggered';
                } catch(e) {
                    return 'Error: ' + e.message;
                }
            }''')
            
            log(f"点击结果: {click_result}")
            await page.wait_for_timeout(3000)
            
            # 检查当前URL
            current_url = page.url
            log(f"当前URL: {current_url[:80]}...")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
