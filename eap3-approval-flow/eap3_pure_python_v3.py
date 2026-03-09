#!/usr/bin/env python3
"""
EAP3 XZ38审批自动化 v3.0 - 纯Python实现（基于API+HTML解析）

核心改进：
1. 通过API获取工作台HTML
2. 使用BeautifulSoup解析提取待办数据
3. 无需Playwright浏览器
"""

import requests
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 可选：安装beautifulsoup4用于HTML解析
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing beautifulsoup4...")
    import subprocess
    subprocess.run(["pip", "install", "beautifulsoup4", "-q"])
    from bs4 import BeautifulSoup

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
        """API登录获取SID"""
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
                return True
            else:
                self.log(f"✗ 登录失败: {data.get('message', '未知错误')}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ 登录异常: {e}", "ERROR")
            return False
    
    def get_todos(self) -> List[Dict]:
        """
        获取待办列表 - 通过API+HTML解析
        
         discovered API endpoint:
        GET /r/w?cmd=com.actionsoft.apps.workbench_task&start=1&boxType=1&boxName=todo&groupName=noGroup
        """
        self.log("获取待办列表...")
        try:
            # 调用工作台任务API（返回HTML）
            resp = self.session.get(
                f"{EAP3_URL}/r/w",
                params={
                    "sid": self.sid,
                    "cmd": "com.actionsoft.apps.workbench_task",
                    "start": 1,
                    "boxType": 1,
                    "boxName": "todo",
                    "groupName": "noGroup"
                },
                timeout=30
            )
            
            # 解析HTML提取待办数据
            html = resp.text
            todos = self._parse_todos_from_html(html)
            
            self.log(f"✓ 找到 {len(todos)} 条待办")
            return todos
            
        except Exception as e:
            self.log(f"✗ 获取待办失败: {e}", "ERROR")
            return []
    
    def _parse_todos_from_html(self, html: str) -> List[Dict]:
        """从HTML中解析待办数据"""
        todos = []
        
        # 方法1: 查找script标签中的数据变量
        # 尝试找到包含待办数据的JavaScript变量
        patterns = [
            r'window\.firstPageData\s*=\s*(\[[^\]]+\])',
            r'var\s+firstPageData\s*=\s*(\[[^\]]+\])',
            r'data\s*:\s*(\[\{[^\]]+\}\])',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "XZ38" in str(item.get("title", "")):
                                todos.append({
                                    "id": item.get("id"),
                                    "title": item.get("title"),
                                    "processInstId": item.get("processInstId"),
                                    "applicant": self._extract_applicant(item.get("title", "")),
                                    "region": self._get_region(self._extract_applicant(item.get("title", "")))
                                })
                except:
                    continue
        
        # 方法2: 使用BeautifulSoup解析HTML表格
        if not todos:
            try:
                soup = BeautifulSoup(html, 'html.parser')
                # 查找包含待办的表格行
                rows = soup.find_all('tr', class_=lambda x: x and 'task' in x.lower())
                for row in rows:
                    cells = row.find_all('td')
                    if cells:
                        title_cell = cells[0] if cells else None
                        if title_cell:
                            title = title_cell.get_text(strip=True)
                            if "XZ38" in title:
                                todos.append({
                                    "title": title,
                                    "applicant": self._extract_applicant(title),
                                    "region": self._get_region(self._extract_applicant(title))
                                })
            except Exception as e:
                self.log(f"BeautifulSoup解析失败: {e}", "WARN")
        
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
    
    def run(self):
        """主运行流程"""
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
        for todo in todos:
            self.log(f"  - {todo.get('title', 'N/A')[:50]} ({todo.get('region', '未知')})")
        
        return True


def main():
    """测试纯Python实现"""
    approver = EAP3PurePython()
    success = approver.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
