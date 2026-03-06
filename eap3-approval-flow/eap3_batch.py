#!/usr/bin/env python3
"""
EAP3 审批 - 批量处理版
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

async def process_one(page, sid, todo, index, total):
    """处理单个待办"""
    task_id = todo.get('id')
    process_inst_id = todo.get('processInstId')
    title = todo.get('title', 'Unknown')[:50]
    
    log(f"\n[{index}/{total}] {title}")
    
    try:
        # 打开详情页
        open_url = f"{EAP3_URL}/r/w?sid={sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={process_inst_id}&taskInstId={task_id}&openState=1"
        await page.goto(open_url, timeout=60000)
        await page.wait_for_timeout(8000)
        
        # 1. 尝试点击"接收办理"（如果还没点击的话）
        try:
            await page.click('button:has-text("接收办理")', timeout=5000)
            log("  ✓ 点击 接收办理")
            await page.wait_for_timeout(3000)
            
            # 点击确认对话框的"确定"
            try:
                await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=3000)
                log("  ✓ 确认接收")
                await page.wait_for_timeout(5000)
            except:
                pass
        except:
            log("  - 已进入编辑模式")
        
        # 2. 选择审批结论
        try:
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
        except Exception as e:
            log(f"  - 选择结论: {e}")
        
        # 3. 填写意见
        try:
            await page.fill('textarea', '已核实，请后台支持', timeout=3000)
            log("  ✓ 填写审批意见")
        except:
            pass
        
        # 4. 点击"办理"
        try:
            await page.click('button.blue:has-text("办理")', timeout=5000)
            log("  ✓ 点击 办理")
            await page.wait_for_timeout(5000)
            
            # 处理可能的确认对话框
            for _ in range(3):  # 最多处理3个对话框
                try:
                    await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=2000)
                    log("  ✓ 确认")
                    await page.wait_for_timeout(2000)
                except:
                    break
        except Exception as e:
            log(f"  - 办理: {e}")
        
        # 截图结果
        await page.screenshot(path=f"/root/.openclaw/logs/eap3_result_{index}.png", full_page=True)
        log(f"  ✓ 完成")
        return True
        
    except Exception as e:
        log(f"  ✗ 失败: {e}")
        return False

async def main():
    log("=" * 50)
    log("EAP3 审批 - 批量处理版")
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
            
            # 批量处理
            success_count = 0
            for i, todo in enumerate(first_page_data, 1):
                if await process_one(page, sid, todo, i, len(first_page_data)):
                    success_count += 1
            
            log(f"\n{'='*50}")
            log(f"完成: {success_count}/{len(first_page_data)} 条审批")
            log(f"{'='*50}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
