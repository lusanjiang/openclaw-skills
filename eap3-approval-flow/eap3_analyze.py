#!/usr/bin/env python3
"""
EAP3 审批 - 直接触发内部函数版
"""

import asyncio
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
    log("EAP3 审批 - 事件分析版")
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
                await page.wait_for_timeout(10000)
            except:
                pass
            
            # 截图
            await page.screenshot(path=f"/root/.openclaw/logs/eap3_analyze_start.png", full_page=True)
            
            # 分析事件监听器
            log("分析事件监听器...")
            frames = page.frames
            
            for idx, frame in enumerate(frames):
                try:
                    # 获取页面中所有可能的事件处理函数
                    events = await frame.evaluate('''() => {
                        const result = {
                            globalClick: null,
                            rowHandlers: [],
                            linkHandlers: [],
                            awsFuncs: Object.keys(window).filter(k => k.startsWith('AWS') || k.startsWith('aws') || k.includes('open') || k.includes('todo')).slice(0, 20),
                            jQueryEvents: typeof $ !== 'undefined' ? Object.keys($._data(document, 'events') || {}) : null
                        };
                        
                        // 查找表格行的点击处理
                        const rows = document.querySelectorAll('tr');
                        rows.forEach((row, i) => {
                            if (row.innerText.includes('XZ38')) {
                                // 尝试获取 jQuery 事件
                                const jqEvents = $ ? $._data(row, 'events') : null;
                                result.rowHandlers.push({
                                    index: i,
                                    hasClick: jqEvents && jqEvents.click ? true : false,
                                    clickHandlers: jqEvents && jqEvents.click ? jqEvents.click.length : 0
                                });
                            }
                        });
                        
                        return result;
                    }''')
                    
                    log(f"Frame {idx}:")
                    log(f"  AWS函数: {events.get('awsFuncs', [])}")
                    log(f"  jQuery事件: {events.get('jQueryEvents', 'None')}")
                    
                    for handler in events.get('rowHandlers', []):
                        log(f"  Row {handler['index']}: click={handler['hasClick']}, handlers={handler['clickHandlers']}")
                    
                except Exception as e:
                    log(f"  Frame {idx} 错误: {e}")
            
            # 尝试直接调用可能的打开函数
            log("\n尝试调用内部函数...")
            
            # 获取待办行
            for frame in frames:
                try:
                    rows = await frame.query_selector_all('tr')
                    for row_idx, row in enumerate(rows):
                        text = await row.inner_text()
                        if 'XZ38' not in text:
                            continue
                        
                        m = re.search(r'XZ38-202\d{5,6}', text)
                        if not m:
                            continue
                        
                        xz38 = m.group(0)
                        log(f"\n尝试打开: {xz38}")
                        
                        # 尝试多种方式打开
                        methods = [
                            # 方式1: 直接触发行的click事件
                            '''(row) => {
                                const event = new MouseEvent('click', { bubbles: true });
                                row.dispatchEvent(event);
                                return 'dispatched';
                            }''',
                            # 方式2: 触发行的mousedown+mouseup+click
                            '''(row) => {
                                ['mousedown', 'mouseup', 'click'].forEach(type => {
                                    const event = new MouseEvent(type, { bubbles: true });
                                    row.dispatchEvent(event);
                                });
                                return 'full click';
                            }''',
                            # 方式3: 如果存在jQuery，触发它的click
                            '''(row) => {
                                if (typeof jQuery !== 'undefined') {
                                    jQuery(row).trigger('click');
                                    return 'jquery click';
                                }
                                return 'no jquery';
                            }''',
                            # 方式4: 查找并点击第一个a标签
                            '''(row) => {
                                const link = row.querySelector('a');
                                if (link) {
                                    link.click();
                                    return 'link click';
                                }
                                return 'no link';
                            }'''
                        ]
                        
                        for method_idx, method in enumerate(methods):
                            try:
                                result = await row.evaluate(method)
                                log(f"  方法{method_idx+1}: {result}")
                                await page.wait_for_timeout(3000)
                                
                                # 检查是否跳转到详情页
                                current_url = page.url
                                if 'cmd=' in current_url and 'workbench' not in current_url:
                                    log(f"  ✓ 成功跳转!")
                                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_{xz38}_open.png", full_page=True)
                                    break
                            except Exception as e:
                                log(f"  方法{method_idx+1}失败: {e}")
                        
                except Exception as e:
                    log(f"  行处理错误: {e}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
