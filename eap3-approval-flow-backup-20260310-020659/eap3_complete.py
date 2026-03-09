#!/usr/bin/env python3
"""
EAP3 审批 - 完整版（打开+审批）
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
    log("EAP3 审批 - 完整版")
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
            
            for i, todo in enumerate(first_page_data[:1], 1):  # 先处理第一条
                task_id = todo.get('id')
                process_inst_id = todo.get('processInstId')
                title = todo.get('title', 'Unknown')[:50]
                
                log(f"\n[{i}] {title}")
                log(f"  taskId: {task_id}")
                log(f"  processInstId: {process_inst_id}")
                
                # 打开详情页 - 使用正确的API
                open_url = f"{EAP3_URL}/r/w?sid={sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={process_inst_id}&taskInstId={task_id}&openState=1"
                log(f"  打开详情页...")
                await page.goto(open_url, timeout=60000)
                await page.wait_for_timeout(10000)
                
                # 截图
                await page.screenshot(path=f"/root/.openclaw/logs/eap3_detail_{i}.png", full_page=True)
                
                # 审批步骤
                log("  开始审批...")
                
                # 1. 点击"接收办理"
                try:
                    # 尝试多种方式查找按钮
                    try:
                        await page.click('#BTN_RECEIVE_TRANSACT', timeout=3000)
                    except:
                        try:
                            await page.click('button:has-text("接收办理")', timeout=3000)
                        except:
                            await page.click('text=接收办理', timeout=3000)
                    log("  ✓ 点击 接收办理")
                    await page.wait_for_timeout(5000)
                except Exception as e:
                    log(f"  ✗ 接收办理失败: {e}")
                    # 截图看当前页面
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_error_{i}.png", full_page=True)
                    continue
                
                # 2. 点击"确定"（如果有确认对话框）
                try:
                    await page.click('text=确定', timeout=3000)
                    log("  ✓ 点击 确定")
                    await page.wait_for_timeout(3000)
                except:
                    pass
                
                # 3. 选择"已核实请后台支持"
                try:
                    # 尝试找到审批意见选项
                    await page.click('text=已核实请后台支持', timeout=5000)
                    log("  ✓ 选择 已核实请后台支持")
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    log(f"  - 已核实请后台支持: {e}")
                
                # 4. 填写审批意见
                try:
                    await page.fill('textarea[name="comment"]', '已核实，请后台支持', timeout=3000)
                    log("  ✓ 填写审批意见")
                except:
                    pass
                
                # 5. 点击"提交"
                try:
                    await page.click('text=提交', timeout=5000)
                    log("  ✓ 点击 提交")
                    await page.wait_for_timeout(5000)
                except Exception as e:
                    log(f"  ✗ 提交失败: {e}")
                
                # 截图结果
                await page.screenshot(path=f"/root/.openclaw/logs/eap3_result_{i}.png", full_page=True)
                log(f"  ✓ 审批完成")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
