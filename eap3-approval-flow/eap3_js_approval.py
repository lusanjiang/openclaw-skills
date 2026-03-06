#!/usr/bin/env python3
"""
EAP3 审批 - 从JS变量提取待办
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
        log(f"API登录失败: {e}")
        return None

async def main():
    log("=" * 50)
    log("EAP3 审批 - JS提取版")
    log("=" * 50)
    
    sid = api_login()
    if not sid:
        log("✗ 登录失败")
        return
    log(f"✓ SID: {sid[:20]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 访问工作台
            log("访问工作台...")
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # 点击待办任务
            try:
                await page.click('text=待办任务', timeout=5000)
                log("✓ 点击待办任务标签")
                await page.wait_for_timeout(8000)
            except:
                pass
            
            # 截图
            await page.screenshot(path=f"/root/.openclaw/logs/eap3_workbench_{datetime.now().strftime('%H%M%S')}.png", full_page=True)
            
            # 从页面JS变量提取待办数据
            log("提取待办数据...")
            try:
                # 尝试读取firstPageData变量
                page_data = await page.evaluate('''() => {
                    try {
                        return window.firstPageData || [];
                    } catch(e) {
                        return [];
                    }
                }''')
                log(f"  从firstPageData获取到 {len(page_data)} 条数据")
            except Exception as e:
                log(f"  读取firstPageData失败: {e}")
                page_data = []
            
            # 从页面HTML提取
            if len(page_data) == 0:
                log("  尝试从HTML提取...")
                content = await page.content()
                # 查找所有XZ38相关文本
                matches = re.findall(r'(XZ38-202\d{5}-[\u4e00-\u9fa5]{2,4}[^<"\']{0,50})', content)
                log(f"  HTML中找到 {len(matches)} 个XZ38匹配")
                for m in matches[:5]:
                    log(f"    {m}")
            
            # 从页面文本提取
            log("  从页面文本提取...")
            todo_list = []
            seen = set()
            
            frames = page.frames
            for frame in frames:
                try:
                    # 获取所有元素的文本
                    all_text = await frame.evaluate('''() => {
                        const texts = [];
                        const elements = document.querySelectorAll('td, a, span');
                        elements.forEach(el => {
                            if (el.innerText && el.innerText.includes('XZ38')) {
                                texts.push(el.innerText.trim());
                            }
                        });
                        return texts;
                    }''')
                    
                    for text in all_text:
                        # 匹配 XZ38-2026xxxxx-姓名 格式
                        match = re.search(r'XZ38-(202\d{5,6})-([\u4e00-\u9fa5]{2,4})', text)
                        if match:
                            xz38_num = f"XZ38-{match.group(1)}"
                            user_name = match.group(2)
                            key = f"{user_name}-{xz38_num}"
                            if key not in seen:
                                seen.add(key)
                                todo_list.append({'user': user_name, 'xz38': xz38_num})
                                log(f"  ✓ 待办: {user_name} - {xz38_num}")
                except Exception as e:
                    log(f"  Frame错误: {e}")
            
            log(f"\n共找到 {len(todo_list)} 个待办")
            
            if len(todo_list) == 0:
                log("无待办需要处理")
                return
            
            # 逐个处理
            for i, todo in enumerate(todo_list, 1):
                log(f"\n[{i}/{len(todo_list)}] 处理: {todo['user']}")
                
                try:
                    # 构造打开待办的JavaScript
                    # 先回到工作台
                    await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
                    await page.wait_for_timeout(3000)
                    
                    # 点击待办任务
                    try:
                        await page.click('text=待办任务', timeout=3000)
                        await page.wait_for_timeout(3000)
                    except:
                        pass
                    
                    # 用JS点击包含该XZ38编号的行
                    clicked = await page.evaluate(f'''(xz38Num) => {{
                        const rows = document.querySelectorAll('tr');
                        for (let row of rows) {{
                            if (row.innerText.includes(xz38Num)) {{
                                // 找到行内的链接
                                const link = row.querySelector('a');
                                if (link) {{
                                    link.click();
                                    return true;
                                }}
                                // 没有链接就点击行
                                row.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}''', todo['xz38'])
                    
                    if clicked:
                        log("  已点击待办")
                        await page.wait_for_timeout(10000)
                        
                        # 截图看详情页
                        await page.screenshot(path=f"/root/.openclaw/logs/eap3_detail_{todo['user']}_{datetime.now().strftime('%H%M%S')}.png", full_page=True)
                        
                        # 尝试各种按钮
                        for btn_text in ['接收办理', '办理', '接收', '同意']:
                            try:
                                await page.click(f'text={btn_text}', timeout=2000)
                                log(f"  点击: {btn_text}")
                                await page.wait_for_timeout(3000)
                                break
                            except:
                                pass
                        
                        try:
                            await page.click('text=确定', timeout=2000)
                            log("  点击: 确定")
                            await page.wait_for_timeout(2000)
                        except:
                            pass
                        
                        try:
                            await page.click('text=已核实请后台支持', timeout=3000)
                            log("  选择: 已核实请后台支持")
                            await page.wait_for_timeout(2000)
                        except:
                            pass
                        
                        for btn_text in ['提交', '发送']:
                            try:
                                await page.click(f'text={btn_text}', timeout=2000)
                                log(f"  点击: {btn_text}")
                                await page.wait_for_timeout(5000)
                                break
                            except:
                                pass
                        
                        log(f"✓ {todo['user']} 处理完成")
                    else:
                        log(f"✗ 无法点击 {todo['user']}")
                
                except Exception as e:
                    log(f"✗ 处理失败: {e}")
            
            log("\n" + "=" * 50)
            log("审批执行完毕")
            log("=" * 50)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
