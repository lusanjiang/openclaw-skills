#!/usr/bin/env python3
"""
EAP3 完整审批流程 - 浏览器自动化版
流程: 登录 → 获取待办 → 审批 → 记录飞书
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

# 配置
EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"
FEISHU_DOC_ID = "Otlxd1AllogLYAxzPq4casnRnpb"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def approve_eap3_todos():
    """完整审批流程"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            # 1. 登录
            log("登录EAP3...")
            await page.goto(f"{EAP3_URL}/", wait_until='domcontentloaded', timeout=120000)
            await page.wait_for_timeout(10000)  # 等待页面加载
            
            # 填写账号密码
            inputs = await page.query_selector_all('input')
            if len(inputs) >= 2:
                await inputs[0].fill(USER_ID)
                await inputs[1].fill(ENCRYPTED_PWD)
            
            # 点击登录按钮（尝试多种方式）
            buttons = await page.query_selector_all('button, input[type=submit]')
            for btn in buttons:
                try:
                    text = await btn.inner_text()
                    if '登录' in text:
                        await btn.click()
                        break
                except:
                    pass
            else:
                if buttons:
                    await buttons[0].click()
            
            # 等待登录成功
            await page.wait_for_load_state('networkidle', timeout=120000)
            await page.wait_for_timeout(10000)
            
            url = page.url
            log(f"当前URL: {url[:60]}")
            
            # 检查是否登录成功
            content = await page.content()
            if '待办任务' not in content and '工作台' not in content:
                log("✗ 登录可能失败，保存截图")
                await page.screenshot(path='/tmp/eap3_login_fail.png')
                await browser.close()
                return []
            
            log("✓ 登录成功")
            
            # 2. 获取待办列表
            log("获取待办列表...")
            
            # 查找所有待办项
            todos = []
            links = await page.query_selector_all('a, .task-item, .todo-item')
            
            for link in links:
                try:
                    text = await link.inner_text()
                    if 'XZ38' in text and '定制' in text:
                        # 提取人名
                        names = re.findall(r'([\u4e00-\u9fa5]{2,4})', text)
                        user_name = names[0] if names else "未知"
                        todos.append({
                            'element': link,
                            'user': user_name,
                            'text': text[:100]
                        })
                except:
                    pass
            
            log(f"发现 {len(todos)} 条XZ38待办")
            
            # 3. 逐个审批
            approved_list = []
            for i, todo in enumerate(todos, 1):
                log(f"\n[{i}/{len(todos)}] 审批 {todo['user']}...")
                
                try:
                    # 点击进入待办详情
                    await todo['element'].click()
                    await page.wait_for_timeout(8000)
                    
                    # 点击接收办理
                    receive_btn = await page.query_selector('button:has-text("接收办理"), .btn-receive')
                    if receive_btn:
                        await receive_btn.click()
                        await page.wait_for_timeout(3000)
                        
                        # 确认
                        ok_btn = await page.query_selector('button:has-text("确定"), .btn-ok')
                        if ok_btn:
                            await ok_btn.click()
                            await page.wait_for_timeout(3000)
                    
                    # 选择审批选项
                    try:
                        await page.click('text=已核实请后台支持')
                        await page.wait_for_timeout(2000)
                    except:
                        # 尝试radio按钮
                        radios = await page.query_selector_all('input[type=radio]')
                        for radio in radios:
                            try:
                                value = await radio.get_attribute('value')
                                if '核实' in str(value):
                                    await radio.click()
                                    break
                            except:
                                pass
                    
                    # 点击办理
                    submit_btn = await page.query_selector('button:has-text("办理"), button:has-text("提交")')
                    if submit_btn:
                        await submit_btn.click()
                        await page.wait_for_timeout(5000)
                    
                    # 记录成功
                    approved_list.append({
                        'user': todo['user'],
                        'text': todo['text'],
                        'time': datetime.now().isoformat(),
                        'status': 'approved'
                    })
                    log(f"✓ {todo['user']} 审批完成")
                    
                    # 返回待办列表
                    await page.goto(f"{EAP3_URL}/r/w?cmd=com.actionsoft.apps.workbench_main_page", timeout=60000)
                    await page.wait_for_timeout(5000)
                    
                except Exception as e:
                    log(f"✗ {todo['user']} 审批失败: {e}")
                    approved_list.append({
                        'user': todo['user'],
                        'text': todo['text'],
                        'time': datetime.now().isoformat(),
                        'status': 'failed',
                        'error': str(e)
                    })
                    continue
            
            return approved_list
            
        except Exception as e:
            log(f"流程异常: {e}")
            await page.screenshot(path='/tmp/eap3_error.png')
            return []
        finally:
            await browser.close()
            log("浏览器已关闭")

async def record_to_feishu(approved_list):
    """记录到飞书文档（简化版，写入本地文件）"""
    if not approved_list:
        log("无记录需要保存")
        return
    
    log(f"\n记录到飞书文档...")
    
    # 生成Markdown格式记录
    md_content = f"## 审批记录 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    md_content += "| 申请人 | 状态 | 时间 |\n"
    md_content += "|--------|------|------|\n"
    
    for item in approved_list:
        status = "✅ 成功" if item['status'] == 'approved' else "❌ 失败"
        md_content += f"| {item['user']} | {status} | {item['time'][:16]} |\n"
    
    # 保存到本地（后续可接入飞书API）
    record_file = f"/root/.openclaw/logs/eap3_approval_{datetime.now().strftime('%Y%m%d')}.md"
    with open(record_file, 'a') as f:
        f.write(md_content + "\n")
    
    log(f"✓ 已保存到: {record_file}")

async def main():
    log("=" * 50)
    log("EAP3 完整审批流程")
    log("=" * 50)
    
    # 执行审批
    approved_list = await approve_eap3_todos()
    
    # 记录结果
    await record_to_feishu(approved_list)
    
    log("\n流程结束")
    log(f"成功: {sum(1 for x in approved_list if x['status'] == 'approved')}")
    log(f"失败: {sum(1 for x in approved_list if x['status'] == 'failed')}")

if __name__ == "__main__":
    asyncio.run(main())
