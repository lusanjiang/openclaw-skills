#!/usr/bin/env python3
"""
EAP3 审批 - 分析点击代码版
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
    log("EAP3 审批 - 分析点击代码版")
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
            
            # 获取frames
            frames = page.frames
            
            # 获取页面完整HTML和JS
            log("\n分析Frame 1...")
            
            html = await frames[1].content()
            
            # 查找所有script标签
            scripts = await frames[1].evaluate('''() => {
                const scripts = document.querySelectorAll('script');
                const results = [];
                scripts.forEach((script, i) => {
                    const text = script.textContent || '';
                    if (text.includes('onclick') || text.includes('openTask') || text.includes('openTodo') || text.includes('firstPageData')) {
                        results.push({
                            index: i,
                            text: text.substring(0, 2000)
                        });
                    }
                });
                return results;
            }''')
            
            log(f"找到 {len(scripts)} 个相关脚本")
            
            # 分析第一个相关脚本
            if scripts:
                script_text = scripts[0]['text']
                log(f"\n脚本内容 (前1000字符):\n{script_text[:1000]}")
                
                # 查找onclick处理函数
                onclick_match = re.search(r'onclick=["\']([^"\']+)["\']', script_text)
                if onclick_match:
                    log(f"\n找到onclick: {onclick_match.group(1)[:200]}")
                
                # 查找函数定义
                func_match = re.search(r'function\s+(\w+)[^{]*\{[^}]*open', script_text, re.DOTALL)
                if func_match:
                    log(f"\n找到函数: {func_match.group(0)[:300]}")
            
            # 查找表格行的onclick
            log("\n分析表格行...")
            rows_info = await frames[1].evaluate('''() => {
                const rows = document.querySelectorAll('tr');
                const results = [];
                rows.forEach((row, i) => {
                    if (row.innerText.includes('XZ38')) {
                        const link = row.querySelector('a');
                        if (link) {
                            results.push({
                                index: i,
                                onclick: link.getAttribute('onclick'),
                                href: link.getAttribute('href'),
                                dataId: link.getAttribute('data-id'),
                                outerHTML: link.outerHTML.substring(0, 500)
                            });
                        }
                    }
                });
                return results;
            }''')
            
            for info in rows_info[:3]:
                log(f"\nRow {info['index']}:")
                log(f"  onclick: {info['onclick'][:200] if info['onclick'] else 'None'}")
                log(f"  href: {info['href']}")
                log(f"  data-id: {info['dataId']}")
                log(f"  HTML: {info['outerHTML'][:200]}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
