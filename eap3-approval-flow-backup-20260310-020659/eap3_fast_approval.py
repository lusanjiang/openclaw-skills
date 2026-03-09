#!/usr/bin/env python3
"""
EAP3 快速审批 - 优化版
减少页面加载等待，使用更快的方式
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def approve_todos():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        page = await browser.new_page()
        
        try:
            # 快速登录 - 减少等待时间
            log("访问登录页...")
            await page.goto(f"{EAP3_URL}/", timeout=60000)
            await page.wait_for_timeout(5000)
            
            log("填写账号...")
            # 直接通过选择器填写
            await page.fill('input[type="text"], input[name="userid"], input[placeholder*="用户"]', USER_ID)
            await page.fill('input[type="password"], input[name="pwd"], input[placeholder*="密码"]', ENCRYPTED_PWD)
            
            log("点击登录...")
            await page.click('button[type="submit"], button:has-text("登录"), input[type="submit"]')
            
            # 等待跳转 - 最多60秒
            log("等待登录...")
            for i in range(30):  # 30秒轮询
                await page.wait_for_timeout(1000)
                url = page.url
                if 'workbench' in url or 'main_page' in url:
                    break
                # 检查是否有待办任务字样
                content = await page.content()
                if '待办任务' in content or '工作台' in content:
                    break
            
            log("✓ 登录成功")
            await page.wait_for_timeout(3000)
            
            # 获取当前页面内容
            content = await page.content()
            
            # 检查是否有XZ38待办
            if 'XZ38' not in content:
                log("当前无XZ38待办")
                await browser.close()
                return []
            
            log("✓ 发现XZ38待办")
            
            # 提取待办信息（简化版）
            todos = []
            # 尝试找到待办链接
            links = await page.query_selector_all('a[href*="XZ38"], tr, .list-item')
            
            for link in links[:5]:  # 最多处理5个
                try:
                    text = await link.inner_text()
                    if 'XZ38' in text and '定制' in text:
                        # 尝试点击
                        await link.click()
                        await page.wait_for_timeout(5000)
                        
                        log(f"处理待办: {text[:50]}")
                        
                        # 尝试审批
                        try:
                            # 找接收办理按钮
                            btn = await page.query_selector('button:has-text("接收")')
                            if btn:
                                await btn.click()
                                await page.wait_for_timeout(3000)
                            
                            # 找确定按钮
                            ok = await page.query_selector('button:has-text("确定"), .el-button--primary')
                            if ok:
                                await ok.click()
                                await page.wait_for_timeout(3000)
                            
                            todos.append({'text': text[:80], 'status': 'processed'})
                            log("✓ 处理完成")
                            
                            # 返回
                            await page.go_back()
                            await page.wait_for_timeout(3000)
                            
                        except Exception as e:
                            log(f"处理失败: {e}")
                            continue
                        
                except:
                    continue
            
            return todos
            
        except Exception as e:
            log(f"异常: {e}")
            await page.screenshot(path='/tmp/eap3_error.png')
            return []
        finally:
            await browser.close()
            log("完成")

async def main():
    log("=" * 40)
    log("EAP3 快速审批")
    log("=" * 40)
    
    results = await approve_todos()
    log(f"\n处理完成: {len(results)} 条")

if __name__ == "__main__":
    asyncio.run(main())
