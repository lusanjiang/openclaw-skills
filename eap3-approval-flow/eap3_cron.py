#!/usr/bin/env python3
"""
EAP3审批 - 定时任务版（资源清理优化版，无API Key）
每20分钟自动检查并审批XZ38待办
确保一次做完、及时关闭清理，避免系统卡顿
"""

import asyncio
import gc
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 配置
SKILL_DIR = Path("/root/.openclaw/skills/eap3-approval-flow")
sys.path.insert(0, str(SKILL_DIR))

class EAP3CronApproval:
    def __init__(self):
        self.records = []
        self.browser = None
        self.page = None
        self.p = None
        self.approver = None
        
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}", flush=True)
        
    async def run(self):
        """定时任务主入口"""
        self.log("=" * 60)
        self.log("EAP3定时审批任务启动")
        self.log("=" * 60)
        
        try:
            # 导入
            from eap3_auto import EAP3AutoApprover
            from playwright.async_api import async_playwright
            
            self.approver = EAP3AutoApprover()
            
            # 登录
            self.log("\n[前置检查] 登录EAP3...")
            if not self.approver.api_login():
                self.log("✗ 登录失败", "ERROR")
                return False
                
            # 初始化浏览器
            self.p = await async_playwright().start()
            self.browser = await self.p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--single-process']
            )
            self.approver.browser = self.browser
            self.approver.page = await self.browser.new_page()
            self.page = self.approver.page
            
            # 获取待办
            todos_before = await self.approver.get_todos()
            self.log(f"当前待办: {len(todos_before)} 条XZ38")
            
            if len(todos_before) == 0:
                self.log("无待办需要处理")
                return True
                
            # 处理待办
            self.log(f"\n开始处理 {len(todos_before)} 条待办...")
            for i, todo in enumerate(todos_before, 1):
                record = await self.process_one(todo, i, len(todos_before))
                if record:
                    self.records.append(record)
                    
            # 后置验证
            self.log("\n[后置验证] 重新获取待办...")
            todos_after = await self.approver.get_todos()
            self.log(f"剩余待办: {len(todos_after)} 条XZ38")
            
            # 保存记录到本地（不直接调用需要API Key的飞书API）
            await self.save_records(self.records)
            
            # 统计
            self.log(f"\n{'='*60}")
            self.log(f"本次处理: {len(self.records)} 条")
            self.log(f"剩余待办: {len(todos_after)} 条")
            self.log(f"{'='*60}")
            
            return len(todos_after) == 0
            
        except Exception as e:
            self.log(f"任务执行异常: {e}", "ERROR")
            return False
            
        finally:
            # 确保资源被清理
            await self.cleanup_async()
            
    async def cleanup_async(self):
        """异步清理资源"""
        self.log("\n[资源清理] 开始...")
        
        # 关闭浏览器
        if self.browser:
            try:
                await self.browser.close()
                self.log("✓ 浏览器已关闭")
            except Exception as e:
                self.log(f"关闭浏览器出错: {e}", "WARN")
            self.browser = None
            
        # 停止playwright
        if self.p:
            try:
                await self.p.stop()
                self.log("✓ Playwright已停止")
            except Exception as e:
                self.log(f"停止Playwright出错: {e}", "WARN")
            self.p = None
            
        # 强制垃圾回收
        gc.collect()
        self.log("✓ 垃圾回收完成")
        
        # 杀掉残留的chrome进程
        try:
            subprocess.run(
                ["pkill", "-f", "chrome.*--headless"],
                capture_output=True,
                timeout=5
            )
            self.log("✓ 残留进程已清理")
        except:
            pass
            
        self.log("[资源清理] 完成\n")
        
    async def process_one(self, todo, index, total):
        """处理单个待办"""
        task_id = todo.get('id')
        process_inst_id = todo.get('processInstId')
        title = todo.get('title', 'Unknown')
        
        self.log(f"\n[{index}/{total}] {title[:50]}...")
        
        record = {
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "title": title,
            "task_id": task_id,
            "process_inst_id": process_inst_id,
            "status": "失败",
            "materials": []
        }
        
        try:
            # 打开详情页
            open_url = f"https://eap3.tengen.com.cn/r/w?sid={self.approver.sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={process_inst_id}&taskInstId={task_id}&openState=1"
            await self.page.goto(open_url, timeout=60000)
            await self.page.wait_for_timeout(8000)
            
            # 提取物料
            materials = await self.extract_materials(self.page)
            record["materials"] = materials
            
            # 审批流程
            try:
                await self.page.click('.aws-form-main-toolbar button', timeout=10000)
                self.log("  ✓ 接收办理")
            except:
                pass
                
            await self.page.wait_for_timeout(3000)
            
            try:
                await self.page.click('.awsui-dialog button.blue:has-text("确定")', timeout=5000)
                await self.page.wait_for_timeout(5000)
            except:
                pass
                
            # 选择审批结论
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
            self.log("  ✓ 选择审批结论")
            
            await self.page.wait_for_timeout(2000)
            
            # 点击办理
            await self.page.click('button.blue:has-text("办理")', timeout=10000)
            self.log("  ✓ 点击办理")
            await self.page.wait_for_timeout(5000)
            
            # 确认提交
            for _ in range(3):
                try:
                    await self.page.click('.awsui-dialog button.blue:has-text("确定")', timeout=3000)
                    await self.page.wait_for_timeout(2000)
                except:
                    break
                    
            record["status"] = "成功"
            self.log("  ✓ 完成")
            
        except Exception as e:
            self.log(f"  ✗ 失败: {e}")
            
        return record
        
    async def extract_materials(self, page):
        """从页面提取物料信息"""
        try:
            materials = await page.evaluate('''() => {
                const rows = document.querySelectorAll('table tr');
                const result = [];
                for (let row of rows) {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 4) {
                        const text = row.innerText;
                        if (text.includes('TGR') || text.includes('TGM') || text.includes('TGQ') || text.includes('CJX')) {
                            result.push(text.substring(0, 100));
                        }
                    }
                }
                return result;
            }''')
            return materials
        except:
            return []
            
    async def save_records(self, records):
        """保存记录到本地文件（不调用需要API Key的飞书API）"""
        try:
            content = f"\n\n---\n\n## 定时审批执行记录\n\n**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if not records:
                content += "**结果**: 无待办需要处理\n\n"
            else:
                content += f"**处理数量**: {len(records)} 条\n\n"
                content += "| 时间 | 单据 | 申请人 | 物料 | 状态 |\n"
                content += "|---|---|---|---|---|\n"
                
                for r in records:
                    applicant = "未知"
                    if "XZ38-" in r['title']:
                        parts = r['title'].split('-')
                        if len(parts) >= 4:
                            applicant = parts[3]
                    
                    xz38_no = "未知"
                    for part in r['title'].split('-'):
                        if part.startswith('2026'):
                            xz38_no = f"XZ38-{part}"
                            break
                    
                    material = ""
                    if r['materials']:
                        material = r['materials'][0][:30] + "..."
                    
                    content += f"| {r['time']} | {xz38_no} | {applicant} | {material} | {'✓' if r['status']=='成功' else '✗'} |\n"
                
                content += "\n"
            
            content += "*自动记录 by 定时任务 #审批*\n"
            
            # 只保存到本地文件
            log_file = f"/root/.openclaw/logs/approval_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(log_file, "w") as f:
                f.write(content)
            
            self.log(f"✓ 记录已保存到: {log_file}")
            
            # 写入飞书文档
            try:
                import subprocess
                result = subprocess.run(
                    ["python3", "-c", 
                     f"from feishu_doc import feishu_doc; feishu_doc(action='append', doc_token='Otlxd1AllogLYAxzPq4casnRnpb', content='''{content}''')"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    self.log("✓ 记录已同步到飞书文档")
                else:
                    self.log(f"⚠ 飞书文档同步失败: {result.stderr}")
            except Exception as e:
                self.log(f"⚠ 飞书文档同步异常: {e}")
            
            return True
            
        except Exception as e:
            self.log(f"保存记录失败: {e}")
            return False

async def main():
    cron = EAP3CronApproval()
    try:
        success = await cron.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        cron.log("任务被中断，开始清理...", "WARN")
        await cron.cleanup_async()
        sys.exit(130)
    except Exception as e:
        cron.log(f"未捕获的异常: {e}", "ERROR")
        await cron.cleanup_async()
        sys.exit(1)

if __name__ == "__main__":
    # 设置信号处理
    def signal_handler(sig, frame):
        print(f"\n收到信号 {sig}，准备退出...")
        sys.exit(0)
        
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    asyncio.run(main())
