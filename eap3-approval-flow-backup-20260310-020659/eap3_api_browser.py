#!/usr/bin/env python3
"""
EAP3 审批 - API登录 + 浏览器操作
先用API获取SID，再用浏览器带SID访问
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
        sid = data.get("data", {}).get("sid")
        return sid
    except Exception as e:
        log(f"API登录失败: {e}")
        return None

async def approve_with_sid(sid):
    """使用SID在浏览器中审批"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 直接访问带SID的工作台
            log("访问工作台...")
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(10000)
            
            url = page.url
            log(f"当前URL: {url[:80]}")
            
            content = await page.content()
            
            # 检查是否成功
            if '待办任务' in content or '工作台' in content or 'XZ38' in content:
                log("✓ 成功进入工作台")
                
                # 检查待办
                if 'XZ38' in content:
                    log("✓ 发现XZ38待办")
                    
                    # 查找并点击待办
                    # 尝试找到包含XZ38的链接
                    links = await page.query_selector_all('a')
                    for link in links:
                        text = await link.inner_text()
                        if 'XZ38' in text and '定制' in text:
                            log(f"点击待办: {text[:50]}")
                            await link.click()
                            await page.wait_for_timeout(8000)
                            
                            # 尝试审批
                            try:
                                # 接收办理
                                btns = await page.query_selector_all('button')
                                for btn in btns:
                                    btn_text = await btn.inner_text()
                                    if '接收' in btn_text:
                                        await btn.click()
                                        await page.wait_for_timeout(3000)
                                        break
                                
                                # 确定
                                for btn in btns:
                                    btn_text = await btn.inner_text()
                                    if '确定' in btn_text:
                                        await btn.click()
                                        await page.wait_for_timeout(3000)
                                        break
                                
                                log("✓ 审批操作完成")
                                
                                # 返回
                                await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
                                await page.wait_for_timeout(5000)
                                
                            except Exception as e:
                                log(f"审批操作失败: {e}")
                            
                            break
                    
                    return True
                else:
                    log("无XZ38待办")
                    return True
            else:
                log("✗ 未能进入工作台")
                await page.screenshot(path='/tmp/eap3_sid_fail.png')
                return False
                
        except Exception as e:
            log(f"异常: {e}")
            return False
        finally:
            await browser.close()

async def main():
    log("=" * 40)
    log("EAP3 审批 - API+浏览器方案")
    log("=" * 40)
    
    # 1. API登录获取SID
    log("API登录...")
    sid = api_login()
    if not sid:
        log("✗ 登录失败")
        return
    log(f"✓ 获取SID: {sid[:20]}...")
    
    # 2. 浏览器审批
    success = await approve_with_sid(sid)
    
    log("流程结束")

if __name__ == "__main__":
    asyncio.run(main())
