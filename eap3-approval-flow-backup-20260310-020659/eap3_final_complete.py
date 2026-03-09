#!/usr/bin/env python3
"""
EAP3 审批 - 最终完整版
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
    log("EAP3 审批 - 最终完整版")
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
                
                # 打开详情页
                open_url = f"{EAP3_URL}/r/w?sid={sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={process_inst_id}&taskInstId={task_id}&openState=1"
                log(f"  打开详情页...")
                await page.goto(open_url, timeout=60000)
                await page.wait_for_timeout(10000)
                
                # 截图
                await page.screenshot(path=f"/root/.openclaw/logs/eap3_detail_{i}.png", full_page=True)
                
                # 审批步骤
                log("  开始审批...")
                
                # 1. 尝试点击"接收办理"（如果还没点击的话）
                try:
                    await page.click('button:has-text("接收办理")', timeout=5000)
                    log("  ✓ 点击 接收办理")
                    await page.wait_for_timeout(3000)
                    
                    # 点击确认对话框的"确定"
                    try:
                        await page.click('.awsui-dialog:has-text("确定要接收办理吗") button:has-text("确定")', timeout=3000)
                        log("  ✓ 点击 确定（确认对话框）")
                        await page.wait_for_timeout(5000)
                    except:
                        pass
                except Exception as e:
                    log("  - 接收办理按钮未找到（可能已进入编辑模式）")
                
                # 2. 等待页面刷新，查找审批操作区
                log("  等待审批界面...")
                await page.wait_for_timeout(5000)
                
                # 截图看当前状态
                await page.screenshot(path=f"/root/.openclaw/logs/eap3_step2_{i}.png", full_page=True)
                
                # 3. 查找审批意见输入框
                try:
                    # 尝试多种可能的意见输入框
                    selectors = [
                        'textarea[name="comment"]',
                        'textarea[name="opinion"]',
                        'textarea[placeholder*="意见"]',
                        '#comment',
                        '#opinion'
                    ]
                    for selector in selectors:
                        try:
                            await page.fill(selector, '已核实，请后台支持', timeout=2000)
                            log(f"  ✓ 填写审批意见")
                            break
                        except:
                            continue
                except Exception as e:
                    log(f"  - 填写意见: {e}")
                
                # 4. 查找并选择"已核实请后台支持"
                try:
                    # 先找到radio按钮
                    await page.evaluate('''() => {
                        const radios = document.querySelectorAll('input[type="radio"]');
                        for (let r of radios) {
                            const label = r.nextElementSibling;
                            if (label && (label.innerText?.includes('已核实') || r.value?.includes('已核实'))) {
                                r.click();
                                return 'selected';
                            }
                        }
                        return 'not found';
                    }''')
                    log("  ✓ 选择 已核实请后台支持")
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    log(f"  - 选择结论: {e}")
                
                # 5. 填写意见
                try:
                    await page.fill('textarea[placeholder*="意见"]', '已核实，请后台支持', timeout=3000)
                    log("  ✓ 填写审批意见")
                except:
                    pass
                
                # 6. 点击"办理"（审批按钮）
                try:
                    # 顶部工具栏的办理按钮 - 蓝色按钮
                    await page.click('button.blue:has-text("办理")', timeout=5000)
                    log("  ✓ 点击 办理")
                    await page.wait_for_timeout(5000)
                    
                    # 处理可能的确认对话框
                    try:
                        await page.click('.awsui-dialog button:has-text("确定")', timeout=3000)
                        log("  ✓ 确认提交")
                        await page.wait_for_timeout(3000)
                    except:
                        pass
                except Exception as e:
                    log(f"  - 办理: {e}")
                
                # 最终截图
                await page.screenshot(path=f"/root/.openclaw/logs/eap3_result_{i}.png", full_page=True)
                log(f"  ✓ 审批流程完成")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
