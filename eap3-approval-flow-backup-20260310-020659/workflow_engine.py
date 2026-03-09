#!/usr/bin/env python3
"""
OpenClaw 工作流执行引擎 v1.0
支持 YAML 工作流定义，节点化执行

学习自 Coze 的工作流设计理念，应用于 OpenClaw
"""

import yaml
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import re

class NodeType(Enum):
    """节点类型"""
    API_CALL = "api_call"
    BROWSER_ACTION = "browser_action"
    CODE = "code"
    SELECTOR = "selector"
    NOTIFY = "notify"
    PYTHON_SCRIPT = "python_script"
    DATABASE_WRITE = "database_write"
    LOG = "log"

class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Node:
    """工作流节点"""
    id: str
    type: NodeType
    name: str
    description: str
    config: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    output: Dict[str, str] = field(default_factory=dict)
    on_error: Optional[Dict] = None
    condition: Optional[str] = None
    branches: Optional[List[Dict]] = None
    
@dataclass
class Workflow:
    """工作流定义"""
    name: str
    version: str
    description: str
    inputs: Dict[str, Any]
    nodes: List[Node]
    on_error: Optional[List[Dict]] = None
    on_success: Optional[List[Dict]] = None

class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self):
        self.context = {}  # 执行上下文，存储节点输出
        self.secrets = {}  # 密钥存储
        self.node_status = {}  # 节点状态追踪
        
    def load_workflow(self, yaml_path: str) -> Workflow:
        """从 YAML 加载工作流"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        nodes = []
        for node_data in data.get('nodes', []):
            node = Node(
                id=node_data['id'],
                type=NodeType(node_data['type']),
                name=node_data['name'],
                description=node_data.get('description', ''),
                config=node_data.get('config', {}),
                depends_on=node_data.get('depends_on', []),
                output=node_data.get('output', {}),
                on_error=node_data.get('on_error'),
                condition=node_data.get('condition'),
                branches=node_data.get('branches')
            )
            nodes.append(node)
        
        return Workflow(
            name=data['name'],
            version=data['version'],
            description=data.get('description', ''),
            inputs=data.get('inputs', {}),
            nodes=nodes,
            on_error=data.get('on_error'),
            on_success=data.get('on_success')
        )
    
    def resolve_dependencies(self, nodes: List[Node]) -> List[Node]:
        """拓扑排序，解决节点依赖顺序"""
        # 简单实现：按依赖关系排序
        sorted_nodes = []
        remaining = nodes.copy()
        resolved = set()
        
        while remaining:
            progress = False
            for node in remaining[:]:
                if all(dep in resolved for dep in node.depends_on):
                    sorted_nodes.append(node)
                    resolved.add(node.id)
                    remaining.remove(node)
                    progress = True
            
            if not progress and remaining:
                raise ValueError(f"循环依赖 detected: {[n.id for n in remaining]}")
        
        return sorted_nodes
    
    def interpolate(self, value: Any) -> Any:
        """变量插值，替换 ${...} 为实际值"""
        if isinstance(value, str):
            # 匹配 ${node.output} 或 ${secrets.KEY}
            pattern = r'\$\{([^}]+)\}'
            
            def replace(match):
                path = match.group(1)
                parts = path.split('.')
                
                if parts[0] == 'secrets':
                    return self.secrets.get(parts[1], '')
                elif parts[0] in self.context:
                    data = self.context[parts[0]]
                    for part in parts[1:]:
                        if isinstance(data, dict):
                            data = data.get(part, '')
                        else:
                            break
                    return str(data) if data is not None else ''
                return match.group(0)
            
            return re.sub(pattern, replace, value)
        elif isinstance(value, dict):
            return {k: self.interpolate(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.interpolate(item) for item in value]
        return value
    
    async def execute_node(self, node: Node) -> Dict[str, Any]:
        """执行单个节点"""
        print(f"[执行节点] {node.name} ({node.type.value})")
        self.node_status[node.id] = NodeStatus.RUNNING
        
        try:
            # 根据节点类型执行
            if node.type == NodeType.API_CALL:
                result = await self._execute_api_call(node)
            elif node.type == NodeType.BROWSER_ACTION:
                result = await self._execute_browser_action(node)
            elif node.type == NodeType.CODE:
                result = await self._execute_code(node)
            elif node.type == NodeType.SELECTOR:
                result = await self._execute_selector(node)
            elif node.type == NodeType.NOTIFY:
                result = await self._execute_notify(node)
            elif node.type == NodeType.PYTHON_SCRIPT:
                result = await self._execute_python_script(node)
            elif node.type == NodeType.LOG:
                result = await self._execute_log(node)
            else:
                raise ValueError(f"未知的节点类型: {node.type}")
            
            self.node_status[node.id] = NodeStatus.SUCCESS
            self.context[node.id] = result
            return result
            
        except Exception as e:
            self.node_status[node.id] = NodeStatus.FAILED
            if node.on_error:
                print(f"  [错误处理] {node.on_error.get('message', str(e))}")
            raise
    
    async def _execute_api_call(self, node: Node) -> Dict:
        """执行 API 调用节点"""
        import requests
        
        config = self.interpolate(node.config)
        url = config['url']
        method = config.get('method', 'GET')
        headers = config.get('headers', {})
        body = config.get('body', {})
        
        print(f"  调用 API: {method} {url}")
        
        if method == 'POST':
            resp = requests.post(url, data=body, headers=headers, timeout=30)
        else:
            resp = requests.get(url, headers=headers, timeout=30)
        
        return {'response': resp.json()}
    
    async def _execute_browser_action(self, node: Node) -> Dict:
        """执行浏览器操作节点"""
        # 这里应该调用 Playwright，简化演示
        print(f"  浏览器操作: {node.config.get('url', 'N/A')}")
        return {'js_result': []}  # 实际实现需要 Playwright
    
    async def _execute_code(self, node: Node) -> Dict:
        """执行代码节点"""
        config = node.config
        code = config.get('code', '')
        
        # 构建执行环境
        inputs = self.context
        outputs = {}
        
        # 执行代码（简化版，实际应该用更安全的方式）
        exec_globals = {'inputs': inputs, 'outputs': outputs}
        exec(code, exec_globals)
        
        return outputs
    
    async def _execute_selector(self, node: Node) -> Dict:
        """执行选择器节点（条件分支）"""
        condition = self.interpolate(node.condition)
        print(f"  条件判断: {condition}")
        
        # 简单条件求值
        result = eval(condition, {}, self.context)
        print(f"  条件结果: {result}")
        
        if result and node.branches:
            # 执行 true 分支的第一个节点
            for branch in node.branches:
                if branch.get('case') == True:
                    branch_nodes = branch.get('nodes', [])
                    for branch_node_data in branch_nodes:
                        # 递归执行分支节点
                        branch_node = Node(
                            id=branch_node_data['id'],
                            type=NodeType(branch_node_data['type']),
                            name=branch_node_data['name'],
                            description=branch_node_data.get('description', ''),
                            config=branch_node_data.get('config', {})
                        )
                        await self.execute_node(branch_node)
        
        return {'condition_result': result}
    
    async def _execute_notify(self, node: Node) -> Dict:
        """执行通知节点"""
        config = self.interpolate(node.config)
        message = config.get('message', '')
        template = config.get('template', message)
        
        print(f"  [通知] {template[:100]}...")
        
        return {'notified': True, 'response': None}
    
    async def _execute_python_script(self, node: Node) -> Dict:
        """执行 Python 脚本节点"""
        import subprocess
        
        script = node.config.get('script', '')
        args = node.config.get('args', [])
        
        print(f"  执行脚本: {script} {' '.join(args)}")
        
        # 实际执行脚本
        cmd = ['python3', script] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    async def _execute_log(self, node: Node) -> Dict:
        """执行日志节点"""
        config = self.interpolate(node.config)
        message = config.get('message', '')
        level = config.get('level', 'info')
        
        print(f"  [{level.upper()}] {message}")
        return {'logged': True}
    
    async def run(self, workflow: Workflow, inputs: Dict[str, Any] = None):
        """运行工作流"""
        print(f"=" * 60)
        print(f"启动工作流: {workflow.name} (v{workflow.version})")
        print(f"=" * 60)
        
        # 初始化上下文
        if inputs:
            self.context['inputs'] = inputs
        
        # 拓扑排序
        sorted_nodes = self.resolve_dependencies(workflow.nodes)
        print(f"节点顺序: {[n.id for n in sorted_nodes]}")
        print()
        
        # 顺序执行节点
        for node in sorted_nodes:
            try:
                result = await self.execute_node(node)
            except Exception as e:
                print(f"  [节点失败] {node.id}: {e}")
                if workflow.on_error:
                    for action in workflow.on_error:
                        print(f"  [错误处理] {action}")
                raise
        
        print()
        print(f"=" * 60)
        print(f"工作流执行完成")
        print(f"=" * 60)
        
        return self.context


async def main():
    """测试工作流引擎"""
    engine = WorkflowEngine()
    
    # 加载工作流
    workflow_path = Path(__file__).parent / "workflow.yaml"
    workflow = engine.load_workflow(str(workflow_path))
    
    # 配置密钥（实际应该从环境变量或安全存储读取）
    engine.secrets = {
        'EAP3_USER': 'lusanjiang',
        'EAP3_PASS': '***',
        'FEISHU_APP_TOKEN': '***',
        'FEISHU_TABLE_ID': '***'
    }
    
    # 运行工作流
    result = await engine.run(workflow, inputs={'action': 'check'})
    
    print("\n执行结果:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
