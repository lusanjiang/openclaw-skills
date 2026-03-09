#!/usr/bin/env python3
"""
EAP3 审批 - 移动端模拟版
严格按照用户流程：接收办理 → 确定 → 已核实请后台支持 → 办理
"""

import asyncio
import requests
from playwright.async_api import async_playwright

EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

def log(msg):
    print(f"[{msg}")

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

async def approve_task(page, sid, process_inst_id, task_id, title, index):
    """审批单个任务"""
    log(f"\n[{index}] {title}")
    
    # 打开详情页
    open_url = f"{EAP3_URL}/r/w?sid={sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={process_inst_id}&taskInstId={task_id}&openState=1"
    await page.goto(open_url, timeout=60000)
    await page.wait_for_timeout(10000)
    
    # 步骤1: 点击"接收办理"按钮
    log("  步骤1: 查找接收办理按钮...")
    try:
        # 尝试多种方式查找
        selectors = [
            'button:has-text("接收办理")',
            '[id*="BTN_RECEIVE"]',
            '.aws-form-main-toolbar button',
            'button.blue'
        ]
        for selector in selectors:
            try:
                await page.click(selector, timeout=3000)
                log(f"    ✓ 点击接收办理 ({selector})")
                break
            except:
                continue
        else:
            log("    - 未找到接收办理按钮")
            return False
    except Exception as e:
        log(f"    ✗ 失败: {e}")
        return False
    
    await page.wait_for_timeout(3000)
    
    # 步骤2: 点击"确定"确认
    log("  步骤2: 确认对话框...")
    try:
        await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=5000)
        log("    ✓ 点击确定")
    except:
        log("    - 无确认对话框")
    
    await page.wait_for_timeout(8000)  # 等待页面变成编辑模式
    
    # 步骤3: 选择"已核实请后台支持"
    log("  步骤3: 选择审批结论...")
    try:
        # 尝试点击radio按钮旁边的文字
        result = await page.evaluate('''() => {
            // 方法1: 查找label文字
            const labels = document.querySelectorAll('label');
            for (let label of labels) {
                if (label.innerText.includes('已核实请后台支持')) {
                    label.click();
                    return 'clicked label';
                }
            }
            // 方法2: 查找radio
            const radios = document.querySelectorAll('input[type="radio"]');
            for (let r of radios) {
                const lbl = r.nextElementSibling;
                if (lbl && lbl.innerText?.includes('已核实')) {
                    r.click();
                    lbl.click();
                    return 'clicked radio';
                }
                if (r.value?.includes('已核实')) {
                    r.click();
                    return 'clicked by value';
                }
            }
            return 'not found';
        }''')
        log(f"    ✓ {result}")
    except Exception as e:
        log(f"    ✗ 失败: {e}")
    
    await page.wait_for_timeout(2000)
    
    # 步骤4: 点击"办理"
    log("  步骤4: 点击办理...")
    try:
        await page.click('button.blue:has-text("办理")', timeout=10000)
        log("    ✓ 点击办理")
    except Exception as e:
        log(f"    ✗ 失败: {e}")
        return False
    
    await page.wait_for_timeout(5000)
    
    # 步骤5: 确认提交
    log("  步骤5: 确认提交...")
    for i in range(3):
        try:
            await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=3000)
            log(f"    ✓ 确认 {i+1}")
            await page.wait_for_timeout(2000)
        except:
            break
    
    log("  ✓ 完成")
    return True

async def main():
    log("=" * 50)
    log("EAP3 审批 - 移动端模拟版")
    log("=" * 50)
    
    sid = api_login()
    if not sid:
        return
    log(f"✓ SID: {sid[:15]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 访问工作台获取待办
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
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
            
            log(f"\n找到 {len(first_page_data)} 条待办")
            
            for i, todo in enumerate(first_page_data, 1):
                await approve_task(
                    page, sid,
                    todo.get('processInstId'),
                    todo.get('id'),
                    todo.get('title', 'Unknown')[:40],
                    i
                )
            
            log(f"\n{'='*50}")
            log("全部完成")
            log(f"{'='*50}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
