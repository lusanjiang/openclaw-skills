#!/usr/bin/env python3
"""
EAP3 审批 - 基于已知URL模式
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
    log("EAP3 审批 - 手动构造URL")
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
            await page.screenshot(path=f"/root/.openclaw/logs/eap3_manual_start.png", full_page=True)
            
            # 获取待办ID（从表格中提取）
            frames = page.frames
            todos = []
            
            for frame in frames:
                try:
                    # 获取页面HTML
                    html = await frame.content()
                    # 查找所有XZ38编号
                    matches = re.findall(r'XZ38-202\d{5,6}', html)
                    for m in matches:
                        if m not in [t['id'] for t in todos]:
                            todos.append({'id': m})
                except:
                    pass
            
            log(f"\n找到 {len(todos)} 个待办")
            
            # 尝试直接打开每个待办
            # 基于EAP3常见URL模式构造
            for i, todo in enumerate(todos, 1):
                log(f"\n[{i}/{len(todos)}] {todo['id']}")
                
                try:
                    # 尝试构造详情页URL
                    # 常见的EAP3流程URL模式
                    urls_to_try = [
                        f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_open_task&taskTitle={todo['id']}",
                        f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_open_todo&id={todo['id']}",
                    ]
                    
                    for url in urls_to_try:
                        log(f"  尝试: {url[:70]}...")
                        await page.goto(url, timeout=30000)
                        await page.wait_for_timeout(5000)
                        
                        # 检查是否成功加载（不是错误页面）
                        title = await page.title()
                        content = await page.content()
                        
                        if '错误' not in content and 'Error' not in content and '不存在' not in content:
                            log(f"  ✓ 成功加载: {title}")
                            await page.screenshot(path=f"/root/.openclaw/logs/eap3_{todo['id']}.png", full_page=True)
                            
                            # 尝试审批
                            for btn, wait in [('接收办理', 3), ('确定', 3), ('已核实请后台支持', 2), ('提交', 5)]:
                                try:
                                    await page.click(f'text={btn}', timeout=3000)
                                    log(f"    ✓ {btn}")
                                    await page.wait_for_timeout(wait * 1000)
                                except:
                                    pass
                            
                            log(f"  ✓ 完成")
                            break
                        else:
                            log(f"  ✗ 错误页面")
                    
                except Exception as e:
                    log(f"✗ 失败: {e}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
