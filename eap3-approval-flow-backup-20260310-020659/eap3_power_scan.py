#!/usr/bin/env python3
"""
EAP3 强力待办检测 - 截图+多接口扫描
解决API检测不到但页面显示有的问题
"""

import asyncio
import requests
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def api_login():
    """API登录"""
    try:
        session = requests.Session()
        resp = session.post(f"{EAP3_URL}/r/w", data={
            "userid": USER_ID, "pwd": ENCRYPTED_PWD,
            "cmd": "com.actionsoft.apps.tengen.login",
            "deviceType": "pc", "lang": "cn", "pwdEncode": "RSA", "timeZone": "8",
            "_CACHE_LOGIN_TIME_": str(int(datetime.now().timestamp() * 1000))
        }, timeout=30)
        return resp.json().get("data", {}).get("sid")
    except Exception as e:
        log(f"API登录失败: {e}")
        return None

async def scan_all_pages(sid):
    """扫描所有可能包含待办的页面"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        found_todos = []
        
        try:
            # 1. 工作台主页
            log("扫描工作台...")
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(8000)
            
            content = await page.content()
            
            # 检查是否有XZ38
            if 'XZ38' in content:
                log("✓ 工作台发现XZ38")
                
                # 提取所有待办链接
                links = await page.query_selector_all('a, tr[data-task], .task-item')
                for link in links:
                    try:
                        text = await link.inner_text()
                        href = await link.get_attribute('href') or ''
                        if 'XZ38' in text or 'XZ38' in href:
                            found_todos.append({
                                'source': '工作台',
                                'text': text[:100],
                                'href': href,
                                'element': link
                            })
                    except:
                        pass
            
            # 2. 尝试点击"待办任务"标签
            log("尝试点击待办任务标签...")
            try:
                # 尝试各种可能的选择器
                selectors = [
                    'text=待办任务',
                    'a:has-text("待办")',
                    '.tab:has-text("待办")',
                    '[data-tab="todo"]',
                    'li:has-text("待办")'
                ]
                for sel in selectors:
                    try:
                        await page.click(sel, timeout=3000)
                        log(f"  点击成功: {sel}")
                        await page.wait_for_timeout(5000)
                        break
                    except:
                        pass
                
                # 检查点击后的内容
                content2 = await page.content()
                if 'XZ38' in content2:
                    log("✓ 待办标签页发现XZ38")
                    links2 = await page.query_selector_all('a')
                    for link in links2:
                        try:
                            text = await link.inner_text()
                            if 'XZ38' in text:
                                found_todos.append({
                                    'source': '待办标签页',
                                    'text': text[:100],
                                    'element': link
                                })
                        except:
                            pass
            except Exception as e:
                log(f"  点击待办标签失败: {e}")
            
            # 3. 尝试直接访问任务列表
            log("尝试直接访问任务列表...")
            await page.goto(f"{EAP3_URL}/r/jd?sid={sid}&cmd=com.actionsoft.apps.workbench_tasklist", timeout=30000)
            await page.wait_for_timeout(5000)
            
            content3 = await page.content()
            if 'XZ38' in content3:
                log("✓ 任务列表发现XZ38")
            
            # 4. 截图保存用于调试
            await page.screenshot(path='/tmp/eap3_scan.png')
            log("  截图已保存: /tmp/eap3_scan.png")
            
            return found_todos
            
        except Exception as e:
            log(f"扫描异常: {e}")
            return found_todos
        finally:
            await browser.close()

async def approve_todo(sid, todo_info):
    """审批单个待办"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 进入工作台
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # 点击待办
            if 'element' in todo_info:
                await todo_info['element'].click()
            else:
                # 通过文字查找
                await page.click(f'text={todo_info["text"][:30]}')
            
            await page.wait_for_timeout(8000)
            
            # 审批流程
            log("接收办理...")
            btns = await page.query_selector_all('button')
            for btn in btns:
                try:
                    t = await btn.inner_text()
                    if '接收' in t:
                        await btn.click()
                        await page.wait_for_timeout(3000)
                        break
                except:
                    pass
            
            log("确定...")
            for btn in btns:
                try:
                    t = await btn.inner_text()
                    if '确定' in t:
                        await btn.click()
                        await page.wait_for_timeout(3000)
                        break
                except:
                    pass
            
            log("选择审批选项...")
            try:
                await page.click('text=已核实请后台支持', timeout=5000)
            except:
                radios = await page.query_selector_all('input[type=radio]')
                for r in radios:
                    try:
                        v = await r.get_attribute('value')
                        if v and '核实' in v:
                            await r.click()
                            break
                    except:
                        pass
            await page.wait_for_timeout(2000)
            
            log("提交...")
            for btn in btns:
                try:
                    t = await btn.inner_text()
                    if '提交' in t or '办理' in t or '发送' in t:
                        await btn.click()
                        await page.wait_for_timeout(5000)
                        break
                except:
                    pass
            
            log("✓ 审批完成")
            return True
            
        except Exception as e:
            log(f"审批失败: {e}")
            return False
        finally:
            await browser.close()

async def main():
    log("=" * 50)
    log("EAP3 强力待办扫描")
    log("=" * 50)
    
    # 登录
    sid = api_login()
    if not sid:
        log("登录失败")
        return
    log(f"SID: {sid[:25]}...")
    
    # 扫描所有页面
    todos = await scan_all_pages(sid)
    
    if not todos:
        log("\n未找到待办，可能原因：")
        log("1. 待办已处理")
        log("2. 在待阅任务中（只需查看，无需审批）")
        log("3. 需要特定权限才能看到")
        log("\n建议：在PC端EAP3确认待办状态")
        return
    
    log(f"\n发现 {len(todos)} 个待办:")
    for i, t in enumerate(todos, 1):
        log(f"  {i}. [{t['source']}] {t['text'][:60]}")
    
    # 审批第一个
    log(f"\n开始审批第1个...")
    success = await approve_todo(sid, todos[0])
    
    if success:
        log("✓ 审批成功")
    else:
        log("✗ 审批失败")

if __name__ == "__main__":
    asyncio.run(main())
