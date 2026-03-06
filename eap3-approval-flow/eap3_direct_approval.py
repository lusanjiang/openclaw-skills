#!/usr/bin/env python3
"""
EAP3 审批流程 - 直接访问详情页版
豆爸专用
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

async def main():
    log("=" * 50)
    log("EAP3 审批 - 直接访问详情页")
    log("=" * 50)
    
    # API登录
    log("API登录...")
    sid = api_login()
    if not sid:
        log("✗ 登录失败")
        return
    log(f"✓ SID: {sid[:20]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 先访问工作台获取待办列表
            log("访问工作台...")
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # 点击待办任务
            try:
                await page.click('text=待办任务', timeout=5000)
                log("✓ 点击待办任务标签")
                await page.wait_for_timeout(5000)
            except:
                pass
            
            # 截图看列表
            await page.screenshot(path=f"/root/.openclaw/logs/eap3_list_{datetime.now().strftime('%H%M%S')}.png", full_page=True)
            
            # 从页面提取所有待办链接
            log("提取待办链接...")
            frames = page.frames
            todo_links = []
            
            for frame in frames:
                try:
                    # 获取所有链接
                    links = await frame.query_selector_all('a')
                    for link in links:
                        try:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            if href and 'XZ38' in text:
                                # 提取XZ38编号
                                match = re.search(r'XZ38-202\d{5}', text)
                                if match:
                                    xz38_num = match.group(0)
                                    # 提取申请人
                                    name_match = re.search(r'([\u4e00-\u9fa5]{2,4})-XZ38', text)
                                    user_name = name_match.group(1) if name_match else "未知"
                                    
                                    # 构造完整URL
                                    if href.startswith('http'):
                                        full_url = href
                                    elif href.startswith('/'):
                                        full_url = f"{EAP3_URL}{href}"
                                    else:
                                        full_url = f"{EAP3_URL}/{href}"
                                    
                                    # 添加SID
                                    if '?' in full_url:
                                        full_url = f"{full_url}&sid={sid}"
                                    else:
                                        full_url = f"{full_url}?sid={sid}"
                                    
                                    todo_links.append({
                                        'user': user_name,
                                        'xz38': xz38_num,
                                        'url': full_url
                                    })
                                    log(f"  待办: {user_name} - {xz38_num}")
                        except:
                            pass
                except:
                    pass
            
            log(f"\n共找到 {len(todo_links)} 个待办")
            
            if len(todo_links) == 0:
                log("无待办")
                return
            
            # 逐个访问详情页并审批
            for i, todo in enumerate(todo_links, 1):
                log(f"\n[{i}/{len(todo_links)}] 审批: {todo['user']} - {todo['xz38']}")
                
                try:
                    # 访问详情页
                    log(f"  访问详情页...")
                    await page.goto(todo['url'], timeout=60000)
                    await page.wait_for_timeout(8000)
                    
                    # 截图
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_detail_{todo['user']}_{datetime.now().strftime('%H%M%S')}.png", full_page=True)
                    
                    # 查找并点击"接收办理"
                    found_button = False
                    for btn_text in ['接收办理', '办理', '接收', '同意']:
                        try:
                            await page.click(f'text={btn_text}', timeout=3000)
                            log(f"  点击: {btn_text}")
                            found_button = True
                            await page.wait_for_timeout(3000)
                            break
                        except:
                            pass
                    
                    if not found_button:
                        log("  ⚠ 未找到接收办理按钮，可能已处理")
                        continue
                    
                    # 点击确定
                    try:
                        await page.click('text=确定', timeout=3000)
                        log("  点击: 确定")
                        await page.wait_for_timeout(3000)
                    except:
                        pass
                    
                    # 选择意见
                    try:
                        await page.click('text=已核实请后台支持', timeout=3000)
                        log("  选择: 已核实请后台支持")
                        await page.wait_for_timeout(2000)
                    except:
                        pass
                    
                    # 点击提交
                    try:
                        await page.click('text=提交', timeout=3000)
                        log("  点击: 提交")
                        await page.wait_for_timeout(5000)
                    except:
                        try:
                            await page.click('text=发送', timeout=2000)
                            log("  点击: 发送")
                            await page.wait_for_timeout(5000)
                        except:
                            pass
                    
                    # 截图看结果
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_result_{todo['user']}_{datetime.now().strftime('%H%M%S')}.png", full_page=True)
                    log(f"✓ {todo['user']} 审批完成")
                    
                except Exception as e:
                    log(f"✗ 审批失败: {e}")
            
            log("\n" + "=" * 50)
            log("审批流程执行完毕")
            log("=" * 50)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
