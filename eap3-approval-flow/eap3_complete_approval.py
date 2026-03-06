#!/usr/bin/env python3
"""
EAP3 完整审批流程 - 最终版
豆爸专用 - 自动完成审批
"""

import asyncio
import json
import re
import requests
from datetime import datetime
from playwright.async_api import async_playwright

EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"
RECORD_FILE = "/root/.openclaw/logs/eap3_approval_records.json"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def api_login():
    """API登录获取SID"""
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
        log(f"API登录失败: {e}")
        return None

async def find_and_click_todo(page, user_name):
    """在工作台找到并点击指定用户的待办"""
    # 等待页面加载
    await page.wait_for_timeout(5000)
    
    # 获取所有frames
    frames = page.frames
    
    for frame in frames:
        try:
            # 查找所有表格行
            rows = await frame.query_selector_all('tr')
            for row in rows:
                try:
                    text = await row.inner_text()
                    # 检查是否包含该用户和XZ38
                    if user_name in text and 'XZ38' in text:
                        # 尝试点击行内的链接
                        links = await row.query_selector_all('a')
                        for link in links:
                            try:
                                href = await link.get_attribute('href')
                                if href:
                                    # 直接导航到链接
                                    full_url = href if href.startswith('http') else f"{EAP3_URL}{href if href.startswith('/') else '/' + href}"
                                    log(f"  导航到: {full_url[:60]}...")
                                    await page.goto(full_url, timeout=60000)
                                    await page.wait_for_timeout(8000)
                                    return True
                            except:
                                pass
                        
                        # 如果没有链接，尝试点击行本身
                        try:
                            await row.click()
                            await page.wait_for_timeout(8000)
                            return True
                        except:
                            pass
                except:
                    pass
        except:
            pass
    
    return False

async def approve_detail_page(page):
    """在详情页完成审批"""
    await page.wait_for_timeout(5000)
    
    # 截图看详情页状态
    screenshot = f"/root/.openclaw/logs/eap3_approval_{datetime.now().strftime('%H%M%S')}.png"
    await page.screenshot(path=screenshot, full_page=True)
    log(f"  详情页截图: {screenshot}")
    
    # 1. 尝试点击"接收办理"
    for btn_text in ['接收办理', '办理', '接收']:
        try:
            # 尝试不同的选择器
            for selector in [f'text={btn_text}', f'button:has-text("{btn_text}")', f'[value="{btn_text}"]']:
                try:
                    await page.click(selector, timeout=2000)
                    log(f"  点击: {btn_text}")
                    await page.wait_for_timeout(3000)
                    break
                except:
                    pass
            else:
                continue
            break
        except:
            pass
    
    # 2. 点击"确定"
    for btn_text in ['确定', '确认']:
        try:
            for selector in [f'text={btn_text}', f'button:has-text("{btn_text}")']:
                try:
                    await page.click(selector, timeout=2000)
                    log(f"  点击: {btn_text}")
                    await page.wait_for_timeout(3000)
                    break
                except:
                    pass
            else:
                continue
            break
        except:
            pass
    
    # 3. 选择意见"已核实请后台支持"
    try:
        # 先点击意见选择区域
        await page.click('text=意见', timeout=3000)
        await page.wait_for_timeout(1000)
    except:
        pass
    
    try:
        await page.click('text=已核实请后台支持', timeout=3000)
        log("  选择意见: 已核实请后台支持")
        await page.wait_for_timeout(2000)
    except:
        # 尝试radio按钮
        try:
            radios = await page.query_selector_all('input[type="radio"]')
            for radio in radios:
                try:
                    value = await radio.get_attribute('value')
                    if value and '核实' in value:
                        await radio.click()
                        log("  选择radio: 已核实请后台支持")
                        await page.wait_for_timeout(2000)
                        break
                except:
                    pass
        except:
            pass
    
    # 4. 点击"提交"
    for btn_text in ['提交', '发送', '确定']:
        try:
            for selector in [f'text={btn_text}', f'button:has-text("{btn_text}")', f'input[type="submit"][value="{btn_text}"]']:
                try:
                    await page.click(selector, timeout=2000)
                    log(f"  点击: {btn_text}")
                    await page.wait_for_timeout(5000)
                    break
                except:
                    pass
            else:
                continue
            break
        except:
            pass
    
    # 截图看结果
    await page.wait_for_timeout(3000)
    result_screenshot = f"/root/.openclaw/logs/eap3_result_{datetime.now().strftime('%H%M%S')}.png"
    await page.screenshot(path=result_screenshot, full_page=True)
    log(f"  结果截图: {result_screenshot}")
    
    return True

async def approve_todos(sid):
    """审批所有待办"""
    approved_list = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 访问工作台
            log("访问工作台...")
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # 点击待办任务标签
            try:
                await page.click('text=待办任务', timeout=5000)
                log("✓ 点击待办任务标签")
                await page.wait_for_timeout(5000)
            except:
                log("待办任务标签未找到")
            
            # 截图
            await page.screenshot(path=f"/root/.openclaw/logs/eap3_start_{datetime.now().strftime('%H%M%S')}.png", full_page=True)
            
            # 获取所有待办
            frames = page.frames
            todo_users = set()
            
            for frame in frames:
                try:
                    rows = await frame.query_selector_all('tr')
                    for row in rows:
                        try:
                            text = await row.inner_text()
                            if 'XZ38' in text:
                                # 提取申请人
                                match = re.search(r'([\u4e00-\u9fa5]{2,4})-XZ38-202\d{5}', text)
                                if match:
                                    user_name = match.group(1)
                                    if user_name not in todo_users:
                                        todo_users.add(user_name)
                                        log(f"  发现待办: {user_name}")
                        except:
                            pass
                except:
                    pass
            
            log(f"\n共找到 {len(todo_users)} 个待办")
            
            if len(todo_users) == 0:
                log("无待办")
                return approved_list
            
            # 逐个审批
            for i, user_name in enumerate(sorted(todo_users), 1):
                log(f"\n[{i}/{len(todo_users)}] 审批: {user_name}")
                
                try:
                    # 返回工作台
                    await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
                    await page.wait_for_timeout(3000)
                    
                    # 点击待办任务
                    try:
                        await page.click('text=待办任务', timeout=3000)
                        await page.wait_for_timeout(3000)
                    except:
                        pass
                    
                    # 找到并点击待办
                    if await find_and_click_todo(page, user_name):
                        # 完成审批
                        await approve_detail_page(page)
                        
                        approved_list.append({
                            'time': datetime.now().isoformat(),
                            'user': user_name,
                            'status': 'approved'
                        })
                        log(f"✓ {user_name} 审批完成")
                    else:
                        log(f"✗ 无法点击 {user_name} 的待办")
                        approved_list.append({
                            'time': datetime.now().isoformat(),
                            'user': user_name,
                            'status': 'failed',
                            'error': '无法点击'
                        })
                
                except Exception as e:
                    log(f"✗ 审批失败: {e}")
                    approved_list.append({
                        'time': datetime.now().isoformat(),
                        'user': user_name,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return approved_list
            
        except Exception as e:
            log(f"异常: {e}")
            return approved_list
        finally:
            await browser.close()

def record_to_file(approved_list):
    """记录到本地文件"""
    if not approved_list:
        return
    
    try:
        import os
        existing = []
        if os.path.exists(RECORD_FILE):
            with open(RECORD_FILE, 'r') as f:
                existing = json.load(f)
        
        existing.extend(approved_list)
        
        with open(RECORD_FILE, 'w') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        log(f"✓ 已记录 {len(approved_list)} 条")
    except Exception as e:
        log(f"记录失败: {e}")

async def main():
    log("=" * 50)
    log("EAP3 完整审批流程")
    log("=" * 50)
    
    # API登录
    log("API登录...")
    sid = api_login()
    if not sid:
        log("✗ 登录失败")
        return
    log(f"✓ 获取SID: {sid[:20]}...")
    
    # 审批
    approved_list = await approve_todos(sid)
    
    # 记录
    if approved_list:
        record_to_file(approved_list)
    
    # 汇总
    log("\n" + "=" * 50)
    success = sum(1 for x in approved_list if x['status'] == 'approved')
    failed = sum(1 for x in approved_list if x['status'] == 'failed')
    log(f"审批完成: 成功 {success}, 失败 {failed}")
    log("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
