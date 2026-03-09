#!/usr/bin/env python3
"""
EAP3 审批 - 拦截点击事件版
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
    log("EAP3 审批 - 事件拦截版")
    log("=" * 50)
    
    sid = api_login()
    if not sid:
        return
    log(f"✓ SID: {sid[:15]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # 拦截所有导航事件
        navigated_urls = []
        def handle_navigate(frame, url):
            navigated_urls.append(url)
            log(f"  导航到: {url[:60]}...")
        
        page.on("framenavigated", handle_navigate)
        
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
            
            # 截图
            await page.screenshot(path=f"/root/.openclaw/logs/eap3_intercept_start.png", full_page=True)
            
            # 获取frames
            frames = page.frames
            log(f"页面有 {len(frames)} 个frame")
            
            # 在iframe中注入点击监听器
            for idx, frame in enumerate(frames):
                try:
                    await frame.evaluate('''() => {
                        window.clickedUrl = null;
                        document.addEventListener('click', function(e) {
                            const link = e.target.closest('a');
                            if (link) {
                                window.clickedUrl = link.href || link.getAttribute('href');
                                console.log('Clicked link:', window.clickedUrl);
                            }
                        }, true);
                    }''')
                except:
                    pass
            
            # 找到所有待办行
            all_rows = []
            for idx, frame in enumerate(frames):
                try:
                    rows = await frame.query_selector_all('tr')
                    for row in rows:
                        text = await row.inner_text()
                        if 'XZ38' in text:
                            m = re.search(r'XZ38-202\d{5,6}', text)
                            if m:
                                all_rows.append({
                                    'xz38': m.group(0),
                                    'frame': frame,
                                    'row': row,
                                    'text': text[:40]
                                })
                except:
                    pass
            
            log(f"\n共 {len(all_rows)} 条待办")
            
            # 逐条点击
            for i, todo in enumerate(all_rows, 1):
                log(f"\n[{i}/{len(all_rows)}] {todo['xz38']}")
                
                try:
                    # 点击前清空记录
                    await todo['frame'].evaluate('() => { window.clickedUrl = null; }')
                    
                    # 点击行
                    await todo['row'].click()
                    log("  已点击")
                    await page.wait_for_timeout(5000)
                    
                    # 获取点击的URL
                    clicked_url = await todo['frame'].evaluate('() => window.clickedUrl')
                    if clicked_url:
                        log(f"  捕获URL: {clicked_url[:60]}...")
                    
                    # 检查是否有导航
                    if navigated_urls:
                        log(f"  导航URL: {navigated_urls[-1][:60]}...")
                        navigated_urls.clear()
                    
                    # 截图
                    await page.screenshot(path=f"/root/.openclaw/logs/eap3_click_{i}.png", full_page=True)
                    
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
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
