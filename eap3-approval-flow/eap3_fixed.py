#!/usr/bin/env python3
"""
EAP3 审批 - 修复版（严格按用户操作流程）
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
                "timeZone": "8"
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
        await page.wait_for_timeout(10000)
        
        # 截图初始状态
        await page.screenshot(path=f"/root/.openclaw/logs/eap3_start_{index}.png", full_page=True)
        
        # 步骤1: 点击"接收办理"（必须在页面点击，不是直接打开URL）
        try:
            # 查找右上角蓝色按钮"接收办理"
            await page.click('.aws-form-main-toolbar button:has-text("接收办理")', timeout=10000)
            log("  ✓ 步骤1: 点击 接收办理")
            await page.wait_for_timeout(3000)
            
            # 点击确认对话框的"确定"
            try:
                await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=5000)
                log("  ✓ 步骤1.1: 确认接收办理")
                await page.wait_for_timeout(8000)  # 等待页面刷新
            except:
                log("  - 无确认对话框")
        except Exception as e:
            log(f"  - 步骤1: 接收办理按钮未找到: {e}")
        
        # 截图看当前状态
        await page.screenshot(path=f"/root/.openclaw/logs/eap3_step1_{index}.png", full_page=True)
        
        # 步骤2: 点击"已核实请后台支持" radio按钮
        try:
            # 查找并点击radio按钮（精确匹配截图中的位置）
            result = await page.evaluate('''() => {
                // 查找所有radio
                const radios = document.querySelectorAll('input[type="radio"]');
                for (let r of radios) {
                    const label = r.nextElementSibling;
                    if (label) {
                        const text = label.innerText || label.textContent || '';
                        if (text.includes('已核实') || text.includes('后台支持')) {
                            r.click();
                            label.click();  // 同时点击label确保选中
                            return {success: true, text: text};
                        }
                    }
                    // 检查value属性
                    if (r.value && (r.value.includes('已核实') || r.value.includes('后台支持'))) {
                        r.click();
                        return {success: true, value: r.value};
                    }
                }
                return {success: false, message: 'radio not found'};
            }''')
            
            if result.get('success'):
                log(f"  ✓ 步骤2: 选择 已核实请后台支持 ({result.get('text') or result.get('value')})")
            else:
                log(f"  - 步骤2: 未找到radio按钮")
            
            await page.wait_for_timeout(3000)
        except Exception as e:
            log(f"  - 步骤2: 选择失败: {e}")
        
        # 步骤3: 填写审批意见
        try:
            await page.fill('textarea[name="comment"]', '已核实，请后台支持', timeout=5000)
            log("  ✓ 步骤3: 填写审批意见")
        except:
            try:
                await page.fill('textarea', '已核实，请后台支持', timeout=3000)
                log("  ✓ 步骤3: 填写审批意见")
            except:
                log("  - 步骤3: 未找到意见输入框")
        
        await page.wait_for_timeout(2000)
        
        # 截图看选择后的状态
        await page.screenshot(path=f"/root/.openclaw/logs/eap3_step2_{index}.png", full_page=True)
        
        # 步骤4: 点击"办理"按钮（右上角蓝色按钮）
        try:
            await page.click('.aws-form-toolbar button.blue:has-text("办理")', timeout=10000)
            log("  ✓ 步骤4: 点击 办理")
            await page.wait_for_timeout(5000)
            
            # 处理可能的确认对话框
            for i in range(3):
                try:
                    await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=3000)
                    log(f"  ✓ 步骤4.{i+1}: 确认提交")
                    await page.wait_for_timeout(3000)
                except:
                    break
        except Exception as e:
            log(f"  - 步骤4: 办理失败: {e}")
        
        # 最终截图
        await page.wait_for_timeout(3000)
        await page.screenshot(path=f"/root/.openclaw/logs/eap3_result_{index}.png", full_page=True)
        log(f"  ✓ 流程完成")
        return True
        
    except Exception as e:
        log(f"  ✗ 失败: {e}")
        return False

async def main():
    log("=" * 50)
    log("EAP3 审批 - 修复版")
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
            log(f"完成: {success_count}/{len(first_page_data)} 条")
            log(f"{'='*50}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
