#!/usr/bin/env python3
"""
EAP3 审批 - 调用内部API版
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
    log("EAP3 审批 - 内部API调用版")
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
            await page.screenshot(path=f"/root/.openclaw/logs/eap3_api_start.png", full_page=True)
            
            # 获取待办数据并调用AWS内部函数
            frames = page.frames
            
            for idx, frame in enumerate(frames):
                try:
                    # 获取页面中所有可能的数据
                    data = await frame.evaluate('''() => {
                        // 查找全局数据变量
                        const result = {
                            firstPageData: window.firstPageData || null,
                            pageData: window.pageData || null,
                            todoData: window.todoData || null,
                            taskList: window.taskList || null
                        };
                        
                        // 尝试从页面脚本标签中提取JSON数据
                        const scripts = document.querySelectorAll('script');
                        let jsonData = null;
                        for (let script of scripts) {
                            const text = script.textContent || '';
                            if (text.includes('XZ38') && text.includes('[')) {
                                try {
                                    const match = text.match(/\[[\s\S]*XZ38[\s\S]*?\]/);
                                    if (match) {
                                        jsonData = match[0];
                                        break;
                                    }
                                } catch(e) {}
                            }
                        }
                        result.scriptData = jsonData ? jsonData.substring(0, 500) : null;
                        
                        return result;
                    }''')
                    
                    if data.get('firstPageData'):
                        log(f"Frame {idx} 找到 firstPageData: {len(data['firstPageData'])} 条")
                        for item in data['firstPageData']:
                            log(f"  {json.dumps(item, ensure_ascii=False)[:100]}")
                    
                    if data.get('scriptData'):
                        log(f"Frame {idx} 从脚本找到数据: {data['scriptData'][:200]}...")
                    
                except Exception as e:
                    pass
            
            # 尝试调用 AWS 内部函数打开任务
            log("\n尝试调用 AWS 函数...")
            
            # 获取表格中的所有数据
            for frame in frames:
                try:
                    # 获取行数据
                    rows_data = await frame.evaluate('''() => {
                        const rows = document.querySelectorAll('table tr');
                        const result = [];
                        rows.forEach((row, idx) => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length > 3) {
                                const text = row.innerText;
                                if (text.includes('XZ38')) {
                                    // 提取所有data属性
                                    const dataAttrs = {};
                                    for (let attr of row.attributes || []) {
                                        if (attr.name.startsWith('data-')) {
                                            dataAttrs[attr.name] = attr.value;
                                        }
                                    }
                                    result.push({
                                        index: idx,
                                        text: text.substring(0, 100),
                                        dataAttrs: dataAttrs,
                                        cellCount: cells.length
                                    });
                                }
                            }
                        });
                        return result;
                    }''')
                    
                    for row_data in rows_data:
                        log(f"\nRow {row_data['index']}: {row_data['text'][:50]}...")
                        log(f"  data属性: {json.dumps(row_data['dataAttrs'], ensure_ascii=False)}")
                        
                        # 尝试构造打开URL
                        # 从文本中提取XZ38编号
                        m = re.search(r'XZ38-202\d{5,6}', row_data['text'])
                        if m:
                            xz38 = m.group(0)
                            
                            # 构造打开待办的URL
                            # 尝试使用 AWSUI 的 openTask 功能
                            open_result = await frame.evaluate(f'''
                                () => {{
                                    try {{
                                        // 尝试调用可能的打开函数
                                        if (typeof openTask === 'function') {{
                                            openTask('{xz38}');
                                            return 'openTask called';
                                        }}
                                        if (typeof awsOpenTask === 'function') {{
                                            awsOpenTask('{xz38}');
                                            return 'awsOpenTask called';
                                        }}
                                        if (window.AWSUI && typeof window.AWSUI.openTask === 'function') {{
                                            window.AWSUI.openTask('{xz38}');
                                            return 'AWSUI.openTask called';
                                        }}
                                        
                                        // 尝试通过 location 跳转
                                        const url = '/r/w?sid=' + encodeURIComponent('{sid}') + 
                                                   '&cmd=com.actionsoft.apps.workbench_open_task' +
                                                   '&taskId=' + encodeURIComponent('{xz38}');
                                        window.location.href = url;
                                        return 'location changed to: ' + url;
                                    }} catch(e) {{
                                        return 'Error: ' + e.message;
                                    }}
                                }}
                            ''')
                            
                            log(f"  打开结果: {open_result}")
                            await page.wait_for_timeout(5000)
                            
                except Exception as e:
                    log(f"  错误: {e}")
            
            log("\n执行完毕")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
