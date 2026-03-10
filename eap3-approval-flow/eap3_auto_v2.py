#!/usr/bin/env python3
"""
EAP3 XZ38审批自动化 v2.0 - 区域筛选+确认模式
福建/江西人员：发送通知等待确认（并发物料信息）
其他省份（含浙江）：自动审批
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
PENDING_FILE = Path("/tmp/eap3_pending_approval.json")
REQUIRED_PACKAGES = ["playwright", "requests"]

# 福建/江西人员名单（需要确认）
FUJIAN_USERS = ["茅智伟", "谢品", "林志伟", "吴国强", "黄丽萍", "何超阳", "唐悠梅"]
JIANGXI_USERS = ["肖培坤", "程明锦", "李志辉", "江伟康", "熊澄伟", "刘荣德", "胡洪箭", "朱海平", "陈毅"]
REGIONAL_USERS = set(FUJIAN_USERS + JIANGXI_USERS)

class EAP3AutoApproverV2:
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
        
        for pkg in REQUIRED_PACKAGES:
            try:
                __import__(pkg)
            except ImportError:
                self.log(f"安装缺失的包: {pkg}", "WARN")
                subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], check=True)
                
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
        
    def extract_applicant(self, title):
        """从标题提取申请人姓名"""
        # 格式: (区域OPS)XZ38-定制及新产品需求-姓名-XZ38-编号...
        try:
            parts = title.split('-')
            if len(parts) >= 3:
                return parts[2].strip()
        except:
            pass
        return "未知"
        
    def get_region(self, applicant):
        """判断申请人所属区域"""
        if applicant in FUJIAN_USERS:
            return "福建"
        elif applicant in JIANGXI_USERS:
            return "江西"
        else:
            return "其他"
            
    async def get_todos_with_details(self):
        """获取待办列表及详细信息"""
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
        
        # 补充申请人信息
        for todo in first_page_data:
            todo['applicant'] = self.extract_applicant(todo.get('title', ''))
            todo['region'] = self.get_region(todo['applicant'])
            
        return first_page_data
        
    async def extract_form_details(self, todo):
        """打开表单并提取详细信息"""
        task_id = todo.get('id')
        process_inst_id = todo.get('processInstId')
        
        try:
            # 打开详情页
            open_url = f"{EAP3_URL}/r/w?sid={self.sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={process_inst_id}&taskInstId={task_id}&openState=1"
            await self.page.goto(open_url, timeout=60000)
            await self.page.wait_for_timeout(8000)
            
            # 提取表单数据
            form_data = await self.page.evaluate('''() => {
                const data = {};
                
                // 提取单据编号
                const formNoEl = document.querySelector('[name="formNo"]') || 
                                  document.querySelector('input[value*="XZ38"]') ||
                                  document.querySelector('td:contains("XZ38")');
                if (formNoEl) data.formNo = formNoEl.value || formNoEl.textContent;
                
                // 提取客户名称
                const customerLabels = document.querySelectorAll('td, label, div');
                for (let el of customerLabels) {
                    if (el.textContent.includes('客户名称') || el.textContent.includes('客户')) {
                        const nextEl = el.nextElementSibling || el.parentElement.nextElementSibling;
                        if (nextEl) {
                            data.customer = nextEl.textContent.trim();
                            break;
                        }
                    }
                }
                
                // 提取物料表格数据
                const materials = [];
                const tables = document.querySelectorAll('table');
                for (let table of tables) {
                    const headers = table.querySelectorAll('th, td');
                    let hasCustomSeries = false;
                    let hasCustomDesc = false;
                    
                    for (let h of headers) {
                        if (h.textContent.includes('定制系列')) hasCustomSeries = true;
                        if (h.textContent.includes('定制描述')) hasCustomDesc = true;
                    }
                    
                    if (hasCustomSeries && hasCustomDesc) {
                        const rows = table.querySelectorAll('tr');
                        for (let i = 1; i < rows.length; i++) {
                            const cells = rows[i].querySelectorAll('td');
                            if (cells.length >= 4) {
                                materials.push({
                                    series: cells[0]?.textContent?.trim() || '',
                                    company: cells[1]?.textContent?.trim() || '',
                                    env: cells[2]?.textContent?.trim() || '',
                                    description: cells[3]?.textContent?.trim() || ''
                                });
                            }
                        }
                    }
                }
                
                data.materials = materials;
                return data;
            }''')
            
            return form_data
            
        except Exception as e:
            self.log(f"提取表单详情失败: {e}", "WARN")
            return {}
        
    def save_pending_approval(self, todos):
        """保存待确认的审批列表到文件"""
        # 序列化时处理可能的非JSON兼容类型
        serializable_todos = []
        for todo in todos:
            todo_copy = {}
            for k, v in todo.items():
                if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                    todo_copy[k] = v
                else:
                    todo_copy[k] = str(v)
            serializable_todos.append(todo_copy)
        
        pending_data = {
            "timestamp": datetime.now().isoformat(),
            "todos": serializable_todos,
            "count": len(todos)
        }
        with open(PENDING_FILE, 'w', encoding='utf-8') as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=2)
        self.log(f"✓ 已保存 {len(todos)} 条待确认记录到 {PENDING_FILE}")
        
    def load_pending_approval(self):
        """加载待确认的审批列表"""
        if not PENDING_FILE.exists():
            return None
        try:
            with open(PENDING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
            
    def clear_pending_approval(self):
        """清除待确认记录"""
        if PENDING_FILE.exists():
            PENDING_FILE.unlink()
            self.log("✓ 已清除待确认记录")
            
    async def extract_material_info(self):
        """从表单页面提取物料详情"""
        try:
            # 尝试提取物料表格信息
            material_info = await self.page.evaluate('''() => {
                const result = {
                    customSeries: '',
                    customDesc: '',
                    producer: '',
                    customerName: ''
                };
                
                // 查找物料表格
                const tables = document.querySelectorAll('table');
                for (let table of tables) {
                    const rows = table.querySelectorAll('tr');
                    for (let row of rows) {
                        const cells = row.querySelectorAll('td, th');
                        // 查找包含"定制系列"、"定制描述"等的行
                        for (let i = 0; i < cells.length; i++) {
                            const text = cells[i].innerText || '';
                            if (text.includes('定制系列') && i + 1 < cells.length) {
                                result.customSeries = cells[i + 1].innerText?.trim() || '';
                            }
                            if (text.includes('定制描述') && i + 1 < cells.length) {
                                result.customDesc = cells[i + 1].innerText?.trim() || '';
                            }
                            if (text.includes('生产公司') && i + 1 < cells.length) {
                                result.producer = cells[i + 1].innerText?.trim() || '';
                            }
                        }
                    }
                }
                
                // 查找客户名称
                const labels = document.querySelectorAll('label, td, div');
                for (let el of labels) {
                    const text = el.innerText || '';
                    if (text.includes('客户名称')) {
                        const nextEl = el.nextElementSibling;
                        if (nextEl) {
                            result.customerName = nextEl.innerText?.trim() || '';
                        }
                    }
                }
                
                return result;
            }''')
            return material_info
        except Exception as e:
            self.log(f"    提取物料信息失败: {e}", "WARN")
            return {
                'customSeries': '',
                'customDesc': '',
                'producer': '',
                'customerName': ''
            }
            
    async def approve_one(self, todo, index, total):
        """审批单个待办"""
        task_id = todo.get('id')
        process_inst_id = todo.get('processInstId')
        title = todo.get('title', 'Unknown')[:50]
        applicant = todo.get('applicant', '未知')
        region = todo.get('region', '其他')
        
        self.log(f"\n[{index}/{total}] {title}")
        self.log(f"    申请人: {applicant} ({region})")
        
        try:
            open_url = f"{EAP3_URL}/r/w?sid={self.sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={process_inst_id}&taskInstId={task_id}&openState=1"
            await self.page.goto(open_url, timeout=60000)
            await self.page.wait_for_timeout(10000)
            
            # 提取物料信息
            material_info = await self.extract_material_info()
            todo['material_info'] = material_info
            self.log(f"    定制描述: {material_info.get('customDesc', 'N/A')[:50]}...")
            
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
                    
            await self.page.screenshot(path=f"{LOG_DIR}/eap3_done_{index}.png", full_page=True)
            self.log("  ✓ 完成")
            return True
            
        except Exception as e:
            self.log(f"  ✗ 失败: {e}", "ERROR")
            await self.page.screenshot(path=f"{LOG_DIR}/eap3_error_{index}.png", full_page=True)
            return False
            
    async def run(self, approve_pending=False):
        """
        主运行流程
        approve_pending: 是否审批之前保存的待确认列表
        """
        self.log("=" * 50)
        self.log("EAP3 XZ38审批自动化 v2.0 - 区域筛选+确认模式")
        self.log("=" * 50)
        
        # 1. 环境检查
        self.ensure_dependencies()
        self.ensure_directories()
        
        # 2. 登录
        if not self.api_login():
            self.log("登录失败，退出", "ERROR")
            return False
            
        # 3. 如果是审批待确认列表
        if approve_pending:
            pending = self.load_pending_approval()
            if not pending:
                self.log("没有待确认的审批记录")
                return True
                
            self.log(f"\n[待确认审批] 加载 {pending['count']} 条记录...")
            
            await self.init_browser()
            try:
                success_count = 0
                todos = pending['todos']
                for i, todo in enumerate(todos, 1):
                    if await self.approve_one(todo, i, len(todos)):
                        success_count += 1
                        
                self.log("\n" + "=" * 50)
                self.log(f"待确认审批完成: {success_count}/{len(todos)} 条")
                self.log("=" * 50)
                
                self.clear_pending_approval()
                return True
            finally:
                if self.browser:
                    await self.browser.close()
                if self.p:
                    await self.p.stop()
                    
        # 4. 正常流程：检测待办并分类
        await self.init_browser()
        try:
            self.log("\n[检测待办] 获取所有XZ38待办...")
            todos = await self.get_todos_with_details()
            self.log(f"共找到 {len(todos)} 条待办")
            
            if len(todos) == 0:
                self.log("没有待办需要处理")
                return True
                
            # 分类
            regional_todos = [t for t in todos if t['region'] in ['福建', '江西']]
            other_todos = [t for t in todos if t['region'] == '其他']
            
            self.log(f"\n分类结果:")
            self.log(f"  - 福建/江西 (需确认): {len(regional_todos)} 条")
            self.log(f"  - 其他省份 (自动): {len(other_todos)} 条")
            
            # 5. 先处理其他省份（自动审批）
            if other_todos:
                self.log(f"\n[自动审批] 开始处理其他省份 {len(other_todos)} 条...")
                auto_success = 0
                for i, todo in enumerate(other_todos, 1):
                    if await self.approve_one(todo, i, len(other_todos)):
                        auto_success += 1
                self.log(f"✓ 自动审批完成: {auto_success}/{len(other_todos)} 条")
                
            # 6. 处理福建/江西（发送通知等待确认）
            if regional_todos:
                self.log(f"\n[区域待办] 福建/江西共 {len(regional_todos)} 条，提取详情并发送通知...")
                
                # 提取每个待办的详细信息
                for todo in regional_todos:
                    details = await self.extract_form_details(todo)
                    todo['form_details'] = details
                    await self.page.wait_for_timeout(2000)  # 等待页面稳定
                
                # 输出通知信息（会被OpenClaw捕获发送到聊天）
                print("\n" + "=" * 60)
                print("📋 检测到福建/江西区域XZ38待办，请确认是否审批：")
                print("=" * 60)
                
                for i, todo in enumerate(regional_todos, 1):
                    details = todo.get('form_details', {})
                    materials = details.get('materials', [])
                    
                    print(f"\n【{i}】单据编号: {todo.get('title', '未知')}")
                    print(f"    申请人: {todo['applicant']} ({todo['region']})")
                    print(f"    客户名称: {details.get('customer', '未提取到')}")
                    
                    if materials:
                        print(f"    物料详情:")
                        for j, mat in enumerate(materials, 1):
                            print(f"      {j}. 系列: {mat.get('series', 'N/A')}")
                            print(f"         描述: {mat.get('description', 'N/A')}")
                            print(f"         生产公司: {mat.get('company', 'N/A')}")
                    else:
                        print(f"    物料详情: 未能提取，需人工查看")
                        
                print("\n" + "=" * 60)
                print("💡 如需审批，请回复：#审核")
                print("💡 如需跳过，请回复：#跳过")
                print("=" * 60 + "\n")
                
                # 保存待确认列表
                self.save_pending_approval(regional_todos)
                
                self.log("✓ 已发送确认通知，等待用户指令...")
                return True  # 返回成功，等待用户确认
            else:
                self.log("\n✓ 全部处理完成（无福建/江西待办）")
                return True
                
        finally:
            if self.browser:
                await self.browser.close()
            if self.p:
                await self.p.stop()

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--approve-pending', action='store_true', help='审批待确认列表')
    args = parser.parse_args()
    
    approver = EAP3AutoApproverV2()
    success = await approver.run(approve_pending=args.approve_pending)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
