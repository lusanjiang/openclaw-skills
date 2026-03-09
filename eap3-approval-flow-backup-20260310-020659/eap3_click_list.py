#!/usr/bin/env python3
"""
EAP3 审批 - 从待办列表点击版
"""

import asyncio
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
                "timeZone": "8"
            },
            timeout=30
        )
        return resp.json().get("data", {}).get("sid")
    except Exception as e:
        log(f"登录失败: {e}")
        return None

async def main():
    log("=" * 50)
    log("EAP3 审批 - 从待办列表点击版")
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
            
            # 获取待办列表
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
                task_id = todo.get('id')
                title = todo.get('title', 'Unknown')[:40]
                
                log(f"\n[{i}/{len(first_page_data)}] {title}")
                
                # 每次回到工作台
                await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
                await page.wait_for_timeout(3000)
                try:
                    await page.click('text=待办任务', timeout=3000)
                    await page.wait_for_timeout(5000)
                except:
                    pass
                
                # 在iframe中点击该待办行
                try:
                    clicked = await frames[1].evaluate(f'''
                        (taskId) => {{
                            const link = document.getElementById('a-' + taskId);
                            if (link) {{
                                link.click();
                                return 'clicked link';
                            }}
                            // 如果没找到link，尝试找包含taskId的行
                            const rows = document.querySelectorAll('tr');
                            for (let row of rows) {{
                                if (row.innerText.includes(taskId.substring(0, 8))) {{
                                    row.click();
                                    return 'clicked row';
                                }}
                            }}
                            return 'not found';
                        }}
                    ''', task_id)
                    log(f"  点击待办: {clicked}")
                    await page.wait_for_timeout(10000)
                except Exception as e:
                    log(f"  点击失败: {e}")
                    continue
                
                # 截图看当前状态
                await page.screenshot(path=f"/root/.openclaw/logs/eap3_click_{i}.png", full_page=True)
                
                # 查找并点击"接收办理"
                try:
                    await page.click('button:has-text("接收办理")', timeout=5000)
                    log("  ✓ 点击 接收办理")
                    await page.wait_for_timeout(3000)
                    
                    # 确认对话框
                    try:
                        await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=3000)
                        log("  ✓ 确认")
                        await page.wait_for_timeout(8000)
                    except:
                        pass
                except:
                    log("  - 无接收办理按钮（可能已接收）")
                
                # 选择"已核实请后台支持"
                try:
                    await page.click('text=已核实请后台支持', timeout=5000)
                    log("  ✓ 选择 已核实请后台支持")
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    log(f"  - 选择失败: {e}")
                
                # 点击"办理"
                try:
                    await page.click('button.blue:has-text("办理")', timeout=5000)
                    log("  ✓ 点击 办理")
                    await page.wait_for_timeout(5000)
                    
                    # 确认对话框
                    for _ in range(2):
                        try:
                            await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=3000)
                            log("  ✓ 确认提交")
                            await page.wait_for_timeout(3000)
                        except:
                            break
                except Exception as e:
                    log(f"  - 办理失败: {e}")
                
                # 截图结果
                await page.screenshot(path=f"/root/.openclaw/logs/eap3_done_{i}.png", full_page=True)
                log(f"  ✓ 完成")
            
            log(f"\n{'='*50}")
            log(f"全部完成")
            log(f"{'='*50}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
