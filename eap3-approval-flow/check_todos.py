#!/usr/bin/env python3
import asyncio
import requests
from playwright.async_api import async_playwright

EAP3_URL = 'https://eap3.tengen.com.cn'
USER_ID = 'lusanjiang'
ENCRYPTED_PWD = '345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39'

print("检查当前待办...")

# 登录获取SID
resp = requests.post(f'{EAP3_URL}/r/w', data={
    'userid': USER_ID,
    'pwd': ENCRYPTED_PWD,
    'cmd': 'com.actionsoft.apps.tengen.login',
    'deviceType': 'pc',
    'lang': 'cn',
    'pwdEncode': 'RSA',
    'timeZone': '8'
}, timeout=30)
sid = resp.json().get('data', {}).get('sid')
print(f'SID: {sid[:20]}...' if sid else '登录失败')

async def check_todos():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        try:
            await page.goto(f'{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page', timeout=60000)
            await page.wait_for_timeout(5000)
            try:
                await page.click('text=待办任务', timeout=5000)
                await page.wait_for_timeout(8000)
            except:
                pass
            
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
            
            print(f'\n当前待办: {len(first_page_data)} 条XZ38')
            for i, todo in enumerate(first_page_data, 1):
                print(f'[{i}] {todo.get("title", "")[:60]}...')
        finally:
            await browser.close()

if sid:
    asyncio.run(check_todos())
