#!/usr/bin/env python3
"""
EAP3 审批 - 使用openUrl
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
    log("EAP3 审批 - openUrl版")
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
            
            # 获取firstPageData（包含所有字段）
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
                title = todo.get('title', 'Unknown')[:50]
                log(f"\n[{i}/{len(first_page_data)}] {title}")
                
                # 打印所有字段
                log(f"  数据字段: {list(todo.keys())}")
                
                # 查找可能的URL字段
                url_fields = ['openUrl', 'url', 'link', 'href', 'detailUrl', 'taskUrl']
                found_url = None
                for field in url_fields:
                    if field in todo and todo[field]:
                        found_url = todo[field]
                        log(f"  找到 {field}: {found_url[:80]}...")
                        break
                
                if not found_url:
                    # 尝试使用 id 字段（taskInstId）
                    task_id = todo.get('id')
                    if task_id:
                        # 尝试多种可能的API
                        found_url = f"/r/w?cmd=com.actionsoft.apps.workbench&action=openTaskInst&id={task_id}"
                        log(f"  使用taskInstId构造URL: {found_url[:80]}...")
                
                if not found_url:
                    log("  跳过 - 无URL")
                    continue
                
                try:
                    # 打开详情页
                    full_url = found_url if found_url.startswith('http') else f"{EAP3_URL}{found_url}"
                    if '?' in full_url:
                        full_url += f"&sid={sid}"
                    else:
                        full_url += f"?sid={sid}"
                    
                    log(f"  访问: {full_url[:80]}...")
                    await page.goto(full_url, timeout=60000)
                    await page.wait_for_timeout(10000)
                    
                    # 截图
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_detail_{i}.png", full_page=True)
                    
                    # 查找并点击按钮
                    buttons = ['接收办理', '确定', '已核实请后台支持', '提交']
                    for btn in buttons:
                        try:
                            await page.click(f'text={btn}', timeout=3000)
                            log(f"  ✓ {btn}")
                            await page.wait_for_timeout(3000)
                        except:
                            log(f"  - {btn}")
                    
                    log(f"  ✓ 完成")
                    
                except Exception as e:
                    log(f"  ✗ 失败: {e}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
