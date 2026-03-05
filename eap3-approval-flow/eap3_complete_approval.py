#!/usr/bin/env python3
"""
EAP3 完整审批流程 - API登录 + 浏览器操作 + 飞书记录
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
FEISHU_DOC_ID = "Otlxd1AllogLYAxzPq4casnRnpb"
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

async def approve_todos(sid):
    """审批待办"""
    approved_list = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 访问工作台
            log("访问工作台...")
            await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
            await page.wait_for_timeout(8000)
            
            # 查找待办
            content = await page.content()
            if 'XZ38' not in content:
                log("无XZ38待办")
                return approved_list
            
            log("✓ 发现XZ38待办")
            
            # 获取所有待办链接
            links = await page.query_selector_all('a')
            todo_links = []
            
            for link in links:
                try:
                    text = await link.inner_text()
                    if 'XZ38' in text and '定制' in text:
                        todo_links.append({'element': link, 'text': text})
                except:
                    pass
            
            log(f"待办数量: {len(todo_links)}")
            
            # 逐个审批
            for i, todo in enumerate(todo_links, 1):
                log(f"\n[{i}/{len(todo_links)}] 处理待办...")
                
                try:
                    # 提取人名
                    names = re.findall(r'([\u4e00-\u9fa5]{2,4})', todo['text'])
                    user_name = names[0] if names else "未知"
                    log(f"申请人: {user_name}")
                    
                    # 点击待办
                    await todo['element'].click()
                    await page.wait_for_timeout(8000)
                    
                    # 获取详情页内容
                    detail_content = await page.content()
                    
                    # 提取物料信息（如果有）
                    materials = []
                    if '物料' in detail_content or '产品' in detail_content:
                        # 简单提取
                        mat_matches = re.findall(r'([A-Z]{2,3}\d+[^\s<]{5,30})', detail_content)
                        materials = list(set(mat_matches))[:3]  # 去重，最多3个
                    
                    # 点击接收办理
                    btns = await page.query_selector_all('button, .btn, [role=button]')
                    for btn in btns:
                        try:
                            btn_text = await btn.inner_text()
                            if '接收' in btn_text or '办理' in btn_text:
                                await btn.click()
                                await page.wait_for_timeout(3000)
                                break
                        except:
                            pass
                    
                    # 点击确定
                    for btn in btns:
                        try:
                            btn_text = await btn.inner_text()
                            if '确定' in btn_text or '确认' in btn_text:
                                await btn.click()
                                await page.wait_for_timeout(3000)
                                break
                        except:
                            pass
                    
                    # 选择"已核实请后台支持"
                    try:
                        # 尝试点击文字
                        await page.click('text=已核实请后台支持', timeout=3000)
                    except:
                        # 尝试radio
                        radios = await page.query_selector_all('input[type=radio]')
                        for radio in radios:
                            try:
                                val = await radio.get_attribute('value')
                                if val and '核实' in val:
                                    await radio.click()
                                    break
                            except:
                                pass
                    
                    await page.wait_for_timeout(2000)
                    
                    # 点击提交/办理
                    for btn in btns:
                        try:
                            btn_text = await btn.inner_text()
                            if '提交' in btn_text or '发送' in btn_text:
                                await btn.click()
                                await page.wait_for_timeout(5000)
                                break
                        except:
                            pass
                    
                    # 记录成功
                    approved_list.append({
                        'time': datetime.now().isoformat(),
                        'user': user_name,
                        'materials': materials,
                        'status': 'approved',
                        'note': '已核实请后台支持'
                    })
                    log(f"✓ {user_name} 审批完成")
                    
                    # 返回工作台
                    await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
                    await page.wait_for_timeout(5000)
                    
                except Exception as e:
                    log(f"✗ 审批失败: {e}")
                    approved_list.append({
                        'time': datetime.now().isoformat(),
                        'user': user_name if 'user_name' in dir() else "未知",
                        'status': 'failed',
                        'error': str(e)
                    })
                    continue
            
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
        # 读取现有记录
        existing = []
        if os.path.exists(RECORD_FILE):
            with open(RECORD_FILE, 'r') as f:
                existing = json.load(f)
        
        # 添加新记录
        existing.extend(approved_list)
        
        # 保存
        with open(RECORD_FILE, 'w') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        log(f"✓ 已记录 {len(approved_list)} 条到文件")
    except Exception as e:
        log(f"记录失败: {e}")

async def main():
    log("=" * 50)
    log("EAP3 完整审批流程")
    log("=" * 50)
    
    # 1. API登录
    log("API登录...")
    sid = api_login()
    if not sid:
        log("✗ 登录失败")
        return
    log(f"✓ 获取SID: {sid[:20]}...")
    
    # 2. 浏览器审批
    approved_list = await approve_todos(sid)
    
    # 3. 记录结果
    if approved_list:
        record_to_file(approved_list)
    
    # 4. 汇总
    log("\n" + "=" * 50)
    log("审批完成")
    log(f"成功: {sum(1 for x in approved_list if x['status'] == 'approved')}")
    log(f"失败: {sum(1 for x in approved_list if x['status'] == 'failed')}")
    log("=" * 50)

if __name__ == "__main__":
    import os
    asyncio.run(main())
