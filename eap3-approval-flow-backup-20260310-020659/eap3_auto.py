#!/usr/bin/env python3
"""
EAP3 XZ38审批自动化 - 自修复增强版
具备依赖检查、环境初始化、错误恢复能力
"""

import asyncio
import json
import os
import subprocess
import sys
import requests
from datetime import datetime
from pathlib import Path

# 配置
EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"
SKILL_DIR = Path("/root/.openclaw/skills/eap3-approval-flow")
LOG_DIR = Path("/root/.openclaw/logs")
REQUIRED_PACKAGES = ["playwright", "requests"]

class EAP3AutoApprover:
    def __init__(self):
        self.sid = None
        self.browser = None
        self.page = None
        self.p = None
        
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}")
        
    def ensure_dependencies(self):
        """确保所有依赖已安装"""
        self.log("检查依赖环境...")
        
        # 检查Python包
        for pkg in REQUIRED_PACKAGES:
            try:
                __import__(pkg)
            except ImportError:
                self.log(f"安装缺失的包: {pkg}", "WARN")
                subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], check=True)
                
        # 检查playwright浏览器
        try:
            from playwright.async_api import async_playwright
            import asyncio
            async def check_browser():
                async with async_playwright() as p:
                    await p.chromium.launch()
            asyncio.run(check_browser())
        except Exception:
            self.log("安装Playwright浏览器...", "WARN")
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            
        self.log("✓ 依赖环境就绪")
        return True
        
    def ensure_directories(self):
        """确保必要的目录存在"""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        return True
        
    def api_login(self):
        """API登录获取SID"""
        self.log("登录EAP3...")
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
                    "timeZone": "8"
                },
                timeout=30
            )
            data = resp.json()
            self.sid = data.get("data", {}).get("sid")
            if self.sid:
                self.log(f"✓ 登录成功，SID: {self.sid[:15]}...")
                return True
            else:
                self.log(f"✗ 登录失败: {data}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ 登录异常: {e}", "ERROR")
            return False
            
    async def init_browser(self):
        """初始化浏览器"""
        from playwright.async_api import async_playwright
        self.p = await async_playwright().start()
        self.browser = await self.p.chromium.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = await self.browser.new_page()
        self.log("✓ 浏览器初始化完成")
        return True
        
    async def get_todos(self):
        """获取待办列表"""
        await self.page.goto(
            f"{EAP3_URL}/r/w?sid={self.sid}&cmd=com.actionsoft.apps.workbench_main_page",
            timeout=60000
        )
        await self.page.wait_for_timeout(5000)
        
        try:
            await self.page.click('text=待办任务', timeout=5000)
            await self.page.wait_for_timeout(8000)
        except:
            pass
            
        frames = self.page.frames
        first_page_data = await frames[1].evaluate('''() => {
            const data = window.firstPageData || [];
            const flat = [];
            data.forEach(item => {
                if (Array.isArray(item)) flat.push(...item);
                else if (typeof item === 'object') flat.push(item);
            });
            return flat.filter(item => item.title && item.title.includes('XZ38'));
        }''')
        return first_page_data
        
    async def approve_one(self, todo, index, total):
        """审批单个待办"""
        task_id = todo.get('id')
        process_inst_id = todo.get('processInstId')
        title = todo.get('title', 'Unknown')[:50]
        
        self.log(f"\n[{index}/{total}] {title}")
        
        try:
            # 打开详情页
            open_url = f"{EAP3_URL}/r/w?sid={self.sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={process_inst_id}&taskInstId={task_id}&openState=1"
            await self.page.goto(open_url, timeout=60000)
            await self.page.wait_for_timeout(10000)
            
            # 步骤1: 点击"接收办理"
            self.log("  步骤1: 接收办理...")
            try:
                await self.page.click('.aws-form-main-toolbar button', timeout=10000)
                self.log("    ✓ 点击接收办理")
            except Exception as e:
                self.log(f"    - 未找到按钮或已接收: {e}")
                
            await self.page.wait_for_timeout(3000)
            
            # 步骤2: 确认对话框
            self.log("  步骤2: 确认...")
            try:
                await self.page.click('.awsui-dialog button.blue:has-text("确定")', timeout=5000)
                self.log("    ✓ 确认")
                await self.page.wait_for_timeout(5000)
            except:
                self.log("    - 无确认对话框")
                
            # 步骤3: 选择"已核实请后台支持"
            self.log("  步骤3: 选择审批结论...")
            try:
                await self.page.evaluate('''() => {
                    const labels = document.querySelectorAll('label');
                    for (let label of labels) {
                        if (label.innerText.includes('已核实请后台支持')) {
                            label.click();
                            return 'clicked';
                        }
                    }
                    return 'not found';
                }''')
                self.log("    ✓ 选择 已核实请后台支持")
            except Exception as e:
                self.log(f"    - 选择失败: {e}")
                
            await self.page.wait_for_timeout(2000)
            
            # 步骤4: 点击"办理"
            self.log("  步骤4: 办理...")
            try:
                await self.page.click('button.blue:has-text("办理")', timeout=10000)
                self.log("    ✓ 点击办理")
            except Exception as e:
                self.log(f"    ✗ 办理失败: {e}")
                return False
                
            await self.page.wait_for_timeout(5000)
            
            # 步骤5: 确认提交
            self.log("  步骤5: 确认提交...")
            for i in range(3):
                try:
                    await self.page.click('.awsui-dialog button.blue:has-text("确定")', timeout=3000)
                    self.log(f"    ✓ 确认 {i+1}")
                    await self.page.wait_for_timeout(2000)
                except:
                    break
                    
            # 截图记录
            await self.page.screenshot(path=f"{LOG_DIR}/eap3_done_{index}.png", full_page=True)
            self.log("  ✓ 完成")
            return True
            
        except Exception as e:
            self.log(f"  ✗ 失败: {e}", "ERROR")
            await self.page.screenshot(path=f"{LOG_DIR}/eap3_error_{index}.png", full_page=True)
            return False
            
    async def run(self):
        """主运行流程"""
        self.log("=" * 50)
        self.log("EAP3 XZ38审批自动化 - 自修复增强版")
        self.log("=" * 50)
        
        # 1. 环境检查
        self.ensure_dependencies()
        self.ensure_directories()
        
        # 2. 登录
        if not self.api_login():
            self.log("登录失败，退出", "ERROR")
            return False
            
        # 3. 初始化浏览器
        await self.init_browser()
        
        try:
            # 4. 前置检查 - 获取待办数量
            self.log("\n[前置检查] 获取待办列表...")
            todos_before = await self.get_todos()
            self.log(f"当前待办: {len(todos_before)} 条XZ38")
            
            if len(todos_before) == 0:
                self.log("没有待办需要处理")
                return True
                
            # 5. 执行审批
            success_count = 0
            for i, todo in enumerate(todos_before, 1):
                if await self.approve_one(todo, i, len(todos_before)):
                    success_count += 1
                    
            # 6. 后置验证
            self.log("\n[后置验证] 重新获取待办...")
            todos_after = await self.get_todos()
            self.log(f"剩余待办: {len(todos_after)} 条XZ38")
            
            # 7. 结果统计
            self.log("\n" + "=" * 50)
            self.log(f"处理: {success_count}/{len(todos_before)} 条")
            self.log(f"剩余: {len(todos_after)} 条")
            if len(todos_after) == 0:
                self.log("✓ 全部完成")
            else:
                self.log(f"⚠ 还有 {len(todos_after)} 条待处理")
            self.log("=" * 50)
            
            return len(todos_after) == 0
            
        finally:
            if self.browser:
                await self.browser.close()
            if self.p:
                await self.p.stop()

async def main():
    approver = EAP3AutoApprover()
    success = await approver.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
