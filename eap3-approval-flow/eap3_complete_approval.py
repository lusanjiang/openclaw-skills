#!/usr/bin/env python3
"""
EAP3 完整审批流程 - 最终修复版
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
            await page.wait_for_timeout(5000)
            
            # 点击待办任务标签
            try:
                await page.click('text=待办任务', timeout=5000)
                log("✓ 点击待办任务标签")
                await page.wait_for_timeout(5000)
            except:
                log("待办任务标签未找到")
            
            # 截图
            screenshot_path = f"/root/.openclaw/logs/eap3_debug_{datetime.now().strftime('%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            log(f"✓ 截图: {screenshot_path}")
            
            # 等待表格加载
            await page.wait_for_timeout(5000)
            
            # 获取所有frames
            frames = page.frames
            log(f"页面有 {len(frames)} 个frame")
            
            # 收集所有包含XZ38的待办
            todo_list = []
            seen_users = set()
            
            for frame_idx, frame in enumerate(frames):
                try:
                    # 查找所有元素
                    all_elems = await frame.query_selector_all('*')
                    log(f"Frame {frame_idx}: 找到 {len(all_elems)} 个元素")
                    
                    # 调试：输出包含XZ38的元素
                    for elem in all_elems:
                        try:
                            text = await elem.inner_text()
                            if text and 'XZ38' in text:
                                log(f"  Found XZ38: {text[:60]}...")
                            if not text or 'XZ38' not in text:
                                continue
                            
                            # 提取申请人（姓名-XZ38-2026xxxx 或 XZ38-2026xxxx-姓名）
                            # 尝试两种格式
                            match = re.search(r'([\u4e00-\u9fa5]{2,4})-XZ38-202\d{5}', text)
                            if match:
                                user_name = match.group(1)
                            else:
                                match = re.search(r'XZ38-202\d{5}-([\u4e00-\u9fa5]{2,4})', text)
                                if match:
                                    user_name = match.group(1)
                                else:
                                    continue
                            
                            if user_name in seen_users:
                                continue
                            
                            seen_users.add(user_name)
                            
                            # 查找可点击的父元素
                            clickable = elem
                            try:
                                # 向上查找<a>标签
                                parent_a = await elem.evaluate('el => el.closest("a")')
                                if parent_a:
                                    clickable = parent_a
                                    log(f"    找到<a>父元素")
                                else:
                                    # 如果没有<a>，尝试点击<td>或<tr>
                                    parent_td = await elem.evaluate('el => el.closest("td")')
                                    if parent_td:
                                        clickable = parent_td
                                        log(f"    使用<td>元素")
                            except Exception as e:
                                log(f"    查找父元素失败: {e}")
                            
                            todo_list.append({
                                'user': user_name,
                                'text': text.strip()[:100],
                                'element': clickable
                            })
                            log(f"  ✓ 待办: {user_name}")
                            
                        except Exception as e:
                            pass
                            
                except Exception as e:
                    log(f"Frame {frame_idx} 错误: {e}")
            
            log(f"\n共找到 {len(todo_list)} 个待办")
            
            if len(todo_list) == 0:
                log("无待办")
                return approved_list
            
            # 逐个审批
            for i, todo in enumerate(todo_list, 1):
                log(f"\n[{i}/{len(todo_list)}] 处理: {todo['user']}")
                
                try:
                    # 如果不是第一个，重新定位元素
                    if i > 1:
                        log("  重新定位...")
                        found = False
                        current_frames = page.frames
                        for frame in current_frames:
                            try:
                                elems = await frame.query_selector_all('*')
                                for elem in elems:
                                    try:
                                        text = await elem.inner_text()
                                        if text and todo['user'] in text and 'XZ38' in text:
                                            # 找到可点击元素
                                            try:
                                                parent_a = await elem.evaluate('el => el.closest("a")')
                                                if parent_a:
                                                    todo['element'] = parent_a
                                                else:
                                                    todo['element'] = elem
                                            except:
                                                todo['element'] = elem
                                            found = True
                                            break
                                    except:
                                        pass
                                if found:
                                    break
                            except:
                                pass
                        
                        if not found:
                            log(f"  ✗ 重新定位失败")
                            approved_list.append({'user': todo['user'], 'status': 'failed', 'error': '重新定位失败'})
                            continue
                    
                    # 点击元素
                    try:
                        await todo['element'].click()
                        log("  点击元素")
                    except Exception as e:
                        log(f"  点击失败: {e}")
                        try:
                            await todo['element'].evaluate('el => el.click()')
                            log("  JS点击")
                        except:
                            pass
                    
                    await page.wait_for_timeout(10000)
                    
                    # 截图看详情页
                    detail_screenshot = f"/root/.openclaw/logs/eap3_detail_{todo['user']}_{datetime.now().strftime('%H%M%S')}.png"
                    await page.screenshot(path=detail_screenshot, full_page=True)
                    log(f"  详情页: {detail_screenshot}")
                    
                    # 尝试各种可能的按钮文字
                    # 1. 接收/办理
                    for btn_text in ['接收办理', '接收', '办理', '同意', '审批']:
                        try:
                            await page.click(f'text={btn_text}', timeout=2000)
                            log(f"  点击: {btn_text}")
                            await page.wait_for_timeout(3000)
                            break
                        except:
                            pass
                    
                    # 2. 确定
                    try:
                        await page.click('text=确定', timeout=3000)
                        log("  点击: 确定")
                        await page.wait_for_timeout(3000)
                    except:
                        pass
                    
                    # 3. 选择意见
                    try:
                        await page.click('text=已核实请后台支持', timeout=3000)
                        log("  选择意见")
                        await page.wait_for_timeout(2000)
                    except:
                        pass
                    
                    # 4. 提交
                    for btn_text in ['提交', '发送', '确定', '办理']:
                        try:
                            await page.click(f'text={btn_text}', timeout=2000)
                            log(f"  点击: {btn_text}")
                            await page.wait_for_timeout(5000)
                            break
                        except:
                            pass
                    
                    # 记录成功
                    approved_list.append({
                        'time': datetime.now().isoformat(),
                        'user': todo['user'],
                        'status': 'approved'
                    })
                    log(f"✓ {todo['user']} 审批完成")
                    
                    # 返回工作台
                    if i < len(todo_list):
                        log("  返回工作台...")
                        await page.goto(f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
                        await page.wait_for_timeout(5000)
                        try:
                            await page.click('text=待办任务', timeout=3000)
                            await page.wait_for_timeout(3000)
                        except:
                            pass
                    
                except Exception as e:
                    log(f"✗ 审批失败: {e}")
                    approved_list.append({
                        'time': datetime.now().isoformat(),
                        'user': todo['user'],
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
