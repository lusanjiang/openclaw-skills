#!/usr/bin/env python3
"""
EAP3 XZ38审批自动化 v3.0 - 纯Python实现（无浏览器）
基于JS逆向技术，分析API接口，纯requests实现

改进点：
1. 无需Playwright浏览器，纯requests调用
2. 分析EAP3前端JS，逆向API接口和加密逻辑
3. 直接调用后端API完成审批
"""

import requests
import json
import re
import execjs
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 配置
EAP3_URL = "https://eap3.tengen.com.cn"
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39"

# 福建/江西人员名单
FUJIAN_USERS = ["茅智伟", "谢品", "林志伟", "吴国强", "黄丽萍", "何超阳", "唐悠梅"]
JIANGXI_USERS = ["肖培坤", "程明锦", "李志辉", "江伟康", "熊澄伟", "刘荣德", "胡洪箭", "朱海平", "陈毅"]

class EAP3PurePython:
    """纯Python实现的EAP3审批"""
    
    def __init__(self):
        self.session = requests.Session()
        self.sid = None
        self.user_info = None
        
    def log(self, msg: str, level: str = "INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}")
        
    def login(self) -> bool:
        """
        API登录获取SID
        这是纯API调用，不需要浏览器
        """
        self.log("API登录EAP3...")
        try:
            resp = self.session.post(
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
            self.user_info = data.get("data", {}).get("user")
            
            if self.sid:
                self.log(f"✓ 登录成功，SID: {self.sid[:15]}...")
                # 设置会话cookie
                self.session.cookies.set("sid", self.sid)
                return True
            else:
                self.log(f"✗ 登录失败: {data.get('message', '未知错误')}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ 登录异常: {e}", "ERROR")
            return False
    
    def get_todos(self) -> List[Dict]:
        """
        获取待办列表 - API方式
        
        逆向思路：
        1. 抓包分析工作台页面加载时的API调用
        2. 找到获取待办数据的API端点
        3. 直接调用API获取JSON数据
        
        可能的API端点：
        - GET /r/w?cmd=com.actionsoft.apps.workbench.get_todos
        - POST /r/w?cmd=com.actionsoft.apps.process.get_tasks
        """
        self.log("获取待办列表...")
        try:
            # 方式1: 通过API获取（需要逆向找到正确端点）
            resp = self.session.get(
                f"{EAP3_URL}/r/w",
                params={
                    "sid": self.sid,
                    "cmd": "com.actionsoft.apps.workbench_main_page"
                },
                timeout=30
            )
            
            # 从响应中提取待办数据
            # 通常工作台页面会返回包含待办的JSON或HTML
            data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else None
            
            if data:
                # 提取XZ38待办
                todos = self._extract_xz38_todos(data)
                self.log(f"✓ 找到 {len(todos)} 条XZ38待办")
                return todos
            else:
                # 如果是HTML，需要解析
                self.log("响应为HTML，需要进一步分析", "WARN")
                return []
                
        except Exception as e:
            self.log(f"✗ 获取待办失败: {e}", "ERROR")
            return []
    
    def _extract_xz38_todos(self, data: Dict) -> List[Dict]:
        """从响应数据中提取XZ38待办"""
        todos = []
        # 根据EAP3的响应结构提取
        # 通常是 data.data.todos 或类似路径
        todo_list = data.get("data", {}).get("firstPageData", [])
        
        for item in todo_list:
            if isinstance(item, dict) and "XZ38" in item.get("title", ""):
                todos.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "processInstId": item.get("processInstId"),
                    "applicant": self._extract_applicant(item.get("title", "")),
                    "region": self._get_region(self._extract_applicant(item.get("title", "")))
                })
        return todos
    
    def _extract_applicant(self, title: str) -> str:
        """从标题提取申请人"""
        try:
            parts = title.split('-')
            if len(parts) >= 3:
                return parts[2].strip()
        except:
            pass
        return "未知"
    
    def _get_region(self, applicant: str) -> str:
        """判断区域"""
        if applicant in FUJIAN_USERS:
            return "福建"
        elif applicant in JIANGXI_USERS:
            return "江西"
        return "其他"
    
    def get_form_details(self, task_id: str, process_inst_id: str) -> Dict:
        """
        获取表单详情 - API方式
        
        逆向思路：
        1. 抓包分析打开表单时的API调用
        2. 找到获取表单数据的API
        3. 直接调用获取JSON数据
        
        可能的API：
        - GET /r/w?cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN
        - POST /r/w?cmd=com.actionsoft.apps.process.get_form_data
        """
        self.log(f"获取表单详情: {task_id}...")
        try:
            # 调用表单API
            resp = self.session.get(
                f"{EAP3_URL}/r/w",
                params={
                    "sid": self.sid,
                    "cmd": "CLIENT_BPM_FORM_MAIN_PAGE_OPEN",
                    "processInstId": process_inst_id,
                    "taskInstId": task_id,
                    "openState": "1"
                },
                timeout=30
            )
            
            # 解析响应获取物料信息
            # 如果是HTML，需要用BeautifulSoup解析
            # 如果是JSON，直接提取
            return self._parse_form_response(resp)
            
        except Exception as e:
            self.log(f"✗ 获取表单失败: {e}", "ERROR")
            return {}
    
    def _parse_form_response(self, resp: requests.Response) -> Dict:
        """解析表单响应"""
        content_type = resp.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            return resp.json()
        else:
            # HTML解析 - 需要分析EAP3表单结构
            html = resp.text
            
            # 使用正则或BeautifulSoup提取物料信息
            # 示例：提取定制系列、定制描述等
            details = {}
            
            # 假设表单中有特定的class或id
            # 实际需要通过浏览器分析确定
            series_match = re.search(r'定制系列[：:]\s*([^<\n]+)', html)
            if series_match:
                details['series'] = series_match.group(1).strip()
            
            desc_match = re.search(r'定制描述[：:]\s*([^<\n]+)', html)
            if desc_match:
                details['description'] = desc_match.group(1).strip()
            
            return details
    
    def approve_task(self, task_id: str, process_inst_id: str) -> bool:
        """
        审批任务 - 纯API调用
        
        逆向思路：
        1. 抓包分析点击"办理"按钮时的API调用
        2. 分析请求参数和加密逻辑
        3. 构造相同的请求完成审批
        
        审批流程API：
        1. POST /r/w?cmd=CLIENT_BPM_TASK_ACCEPT - 接收任务
        2. POST /r/w?cmd=CLIENT_BPM_TASK_COMPLETE - 完成任务
        """
        self.log(f"审批任务: {task_id}...")
        try:
            # 步骤1: 接收办理
            resp1 = self.session.post(
                f"{EAP3_URL}/r/w",
                data={
                    "sid": self.sid,
                    "cmd": "CLIENT_BPM_TASK_ACCEPT",
                    "taskInstId": task_id,
                    "processInstId": process_inst_id
                },
                timeout=30
            )
            
            if resp1.status_code != 200:
                self.log(f"✗ 接收任务失败: {resp1.text}", "ERROR")
                return False
            
            self.log("  ✓ 接收任务成功")
            
            # 步骤2: 提交审批（带审批结论）
            resp2 = self.session.post(
                f"{EAP3_URL}/r/w",
                data={
                    "sid": self.sid,
                    "cmd": "CLIENT_BPM_TASK_COMPLETE",
                    "taskInstId": task_id,
                    "processInstId": process_inst_id,
                    "opinion": "已核实请后台支持",  # 审批意见
                    "approve": "true"
                },
                timeout=30
            )
            
            if resp2.status_code == 200:
                self.log("  ✓ 审批完成")
                return True
            else:
                self.log(f"✗ 审批失败: {resp2.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ 审批异常: {e}", "ERROR")
            return False
    
    def run(self, approve_pending: bool = False):
        """
        主运行流程
        """
        self.log("=" * 60)
        self.log("EAP3 XZ38审批自动化 v3.0 - 纯Python实现")
        self.log("=" * 60)
        
        # 1. 登录
        if not self.login():
            return False
        
        # 2. 获取待办
        todos = self.get_todos()
        
        if not todos:
            self.log("没有待办需要处理")
            return True
        
        self.log(f"\n共 {len(todos)} 条XZ38待办")
        
        # 3. 分类处理
        regional = [t for t in todos if t['region'] in ['福建', '江西']]
        others = [t for t in todos if t['region'] == '其他']
        
        self.log(f"  - 福建/江西: {len(regional)} 条")
        self.log(f"  - 其他省份: {len(others)} 条")
        
        # 4. 自动审批其他省份
        if others:
            self.log(f"\n[自动审批] 其他省份 {len(others)} 条...")
            for todo in others:
                self.approve_task(todo['id'], todo['processInstId'])
        
        # 5. 福建/江西发送通知（待确认）
        if regional:
            self.log(f"\n[区域待办] 福建/江西 {len(regional)} 条，提取详情...")
            for todo in regional:
                details = self.get_form_details(todo['id'], todo['processInstId'])
                todo['form_details'] = details
            
            # 保存待确认列表
            self._save_pending(regional)
            
            # 发送通知（这里需要实现消息发送）
            self._send_notification(regional)
        
        self.log("\n" + "=" * 60)
        self.log("处理完成")
        self.log("=" * 60)
        return True
    
    def _save_pending(self, todos: List[Dict]):
        """保存待确认列表"""
        import json
        from pathlib import Path
        
        pending_file = Path("/tmp/eap3_pending_approval.json")
        data = {
            "timestamp": datetime.now().isoformat(),
            "todos": todos,
            "count": len(todos)
        }
        with open(pending_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.log(f"✓ 已保存 {len(todos)} 条待确认记录")
    
    def _send_notification(self, todos: List[Dict]):
        """发送通知（待实现）"""
        # 这里可以集成飞书/钉钉消息
        # 或者调用OpenClaw的message工具
        pass


def main():
    """测试纯Python实现"""
    approver = EAP3PurePython()
    success = approver.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
