#!/usr/bin/env python3
"""
EAP3 审批 - 从JS变量提取URL版
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
    log("EAP3 审批 - URL提取版")
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
            
            # 从页面提取待办数据
            log("提取待办数据...")
            
            # 方法1: 从firstPageData变量提取
            todos = await page.evaluate('''() => {
                try {
                    if (window.firstPageData && Array.isArray(window.firstPageData)) {
                        return window.firstPageData.map(item => ({
                            id: item.id || '',
                            title: item.title || '',
                            processInstId: item.processInstId || '',
                            taskInstId: item.taskInstId || ''
                        }));
                    }
                } catch(e) {}
                return [];
            }''')
            
            log(f"  从firstPageData获取: {len(todos)} 条")
            
            # 方法2: 从页面HTML提取所有XZ38相关链接
            if len(todos) == 0:
                log("  尝试从HTML提取...")
                content = await page.content()
                
                # 查找包含XZ38的链接
                matches = re.findall(r'href="([^"]*XZ38[^"]*)"', content)
                log(f"  找到 {len(matches)} 个XZ38链接")
                
                # 去重并构造待办列表
                seen = set()
                for href in matches:
                    if href in seen:
                        continue
                    seen.add(href)
                    
                    # 提取XZ38编号
                    m = re.search(r'XZ38-202\d{5,6}', href)
                    if m:
                        todos.append({
                            'id': m.group(0),
                            'href': href
                        })
            
            # 方法3: 从表格行提取
            if len(todos) == 0:
                log("  尝试从表格提取...")
                frames = page.frames
                for frame in frames:
                    try:
                        rows = await frame.query_selector_all('tr')
                        for row in rows:
                            text = await row.inner_text()
                            if 'XZ38' in text:
                                # 尝试获取行的onclick属性
                                onclick = await row.get_attribute('onclick')
                                if onclick:
                                    m = re.search(r'XZ38-202\d{5,6}', text)
                                    if m:
                                        todos.append({
                                            'id': m.group(0),
                                            'onclick': onclick[:100]
                                        })
                    except:
                        pass
            
            log(f"\n共找到 {len(todos)} 个待办")
            for i, todo in enumerate(todos[:10], 1):
                log(f"  [{i}] {json.dumps(todo, ensure_ascii=False)[:80]}...")
            
            if len(todos) == 0:
                log("无待办")
                return
            
            # 尝试审批
            log("\n开始审批...")
            for i, todo in enumerate(todos, 1):
                log(f"\n[{i}/{len(todos)}] {todo.get('id', 'unknown')}")
                
                try:
                    # 构造详情页URL
                    if 'href' in todo and todo['href']:
                        href = todo['href']
                        if href.startswith('http'):
                            detail_url = href
                        elif href.startswith('/'):
                            detail_url = f"{EAP3_URL}{href}"
                        else:
                            detail_url = f"{EAP3_URL}/{href}"
                        
                        # 添加SID
                        if '?' in detail_url:
                            detail_url += f"&sid={sid}"
                        else:
                            detail_url += f"?sid={sid}"
                        
                        log(f"  访问: {detail_url[:60]}...")
                        await page.goto(detail_url, timeout=60000)
                        await page.wait_for_timeout(10000)
                        
                    elif 'onclick' in todo:
                        # 执行onclick
                        log(f"  执行onclick...")
                        await page.evaluate(todo['onclick'])
                        await page.wait_for_timeout(10000)
                    else:
                        log("  无URL或onclick")
                        continue
                    
                    # 截图
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_{i}_{todo.get('id', 'x')}.png", full_page=True)
                    
                    # 审批步骤
                    for btn, wait in [('接收办理', 3), ('确定', 3), ('已核实请后台支持', 2), ('提交', 5)]:
                        try:
                            await page.click(f'text={btn}', timeout=3000)
                            log(f"  ✓ {btn}")
                            await page.wait_for_timeout(wait * 1000)
                        except:
                            pass
                    
                    log(f"✓ 完成")
                    
                except Exception as e:
                    log(f"✗ 失败: {e}")
            
            log("\n审批执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
