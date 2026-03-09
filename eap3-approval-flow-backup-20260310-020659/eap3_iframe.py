#!/usr/bin/env python3
"""
EAP3 审批 - iframe深度操作版
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
    log("EAP3 审批 - iframe深度版")
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
            
            # 截图
            await page.screenshot(path=f"/root/.openclaw/logs/eap3_iframe_start.png", full_page=True)
            
            # 获取所有frames并深入操作
            frames = page.frames
            log(f"页面有 {len(frames)} 个frame")
            
            for idx, frame in enumerate(frames):
                log(f"\nFrame {idx}:")
                try:
                    # 获取frame的URL
                    url = frame.url
                    log(f"  URL: {url[:60] if url else 'None'}...")
                    
                    # 获取所有行
                    rows = await frame.query_selector_all('tr')
                    log(f"  找到 {len(rows)} 行")
                    
                    # 处理每一行
                    for row_idx, row in enumerate(rows):
                        try:
                            text = await row.inner_text()
                            if 'XZ38' not in text:
                                continue
                            
                            log(f"\n  Row {row_idx}: {text[:50]}...")
                            
                            # 获取该行的所有信息
                            row_info = await row.evaluate('''(row) => {
                                const result = {
                                    innerHTML: row.innerHTML.substring(0, 500),
                                    onclick: row.getAttribute('onclick'),
                                    dataId: row.getAttribute('data-id'),
                                    links: []
                                };
                                const links = row.querySelectorAll('a');
                                links.forEach(a => {
                                    result.links.push({
                                        href: a.getAttribute('href'),
                                        onclick: a.getAttribute('onclick'),
                                        text: a.innerText.substring(0, 30)
                                    });
                                });
                                return result;
                            }''')
                            
                            log(f"    onclick: {row_info.get('onclick', 'None')}")
                            log(f"    data-id: {row_info.get('dataId', 'None')}")
                            log(f"    links: {len(row_info.get('links', []))}")
                            
                            for link_idx, link_info in enumerate(row_info.get('links', [])):
                                log(f"      Link {link_idx}: {link_info}")
                            
                            # 如果有onclick，执行它
                            if row_info.get('onclick'):
                                log(f"  执行行onclick...")
                                await row.evaluate('(row) => eval(row.getAttribute("onclick"))')
                                await page.wait_for_timeout(10000)
                                await page.screenshot(path=f"/root/.openclaw/logs/eap3_row{row_idx}_clicked.png", full_page=True)
                            
                        except Exception as e:
                            log(f"    行处理错误: {e}")
                            
                except Exception as e:
                    log(f"  Frame错误: {e}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
