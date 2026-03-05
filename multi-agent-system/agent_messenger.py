#!/usr/bin/env python3
"""
Agent间消息传递系统
实现多Agent协作时的数据传递和状态同步
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable


class AgentMessenger:
    """
    Agent消息传递系统
    
    功能：
    1. Agent间发送消息
    2. 任务状态同步
    3. 数据传递
    4. 结果汇总
    """
    
    def __init__(self):
        self.message_queue = {}  # 消息队列
        self.task_status = {}    # 任务状态
        self.shared_data = {}    # 共享数据
    
    def send_message(self, from_agent: str, to_agent: str, message: Dict) -> bool:
        """
        发送消息给指定Agent
        
        Args:
            from_agent: 发送方Agent名称
            to_agent: 接收方Agent名称
            message: 消息内容
        
        Returns:
            是否发送成功
        """
        msg = {
            'from': from_agent,
            'to': to_agent,
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'status': 'unread'
        }
        
        if to_agent not in self.message_queue:
            self.message_queue[to_agent] = []
        
        self.message_queue[to_agent].append(msg)
        
        print(f"📨 [{from_agent}] → [{to_agent}]: {message.get('type', 'message')}")
        return True
    
    def receive_message(self, agent_name: str, mark_read: bool = True) -> List[Dict]:
        """
        接收消息
        
        Args:
            agent_name: Agent名称
            mark_read: 是否标记为已读
        
        Returns:
            消息列表
        """
        messages = self.message_queue.get(agent_name, [])
        
        if mark_read:
            for msg in messages:
                msg['status'] = 'read'
        
        return messages
    
    def broadcast(self, from_agent: str, message: Dict, exclude: List[str] = None):
        """
        广播消息给所有Agent
        
        Args:
            from_agent: 发送方
            message: 消息内容
            exclude: 排除的Agent列表
        """
        exclude = exclude or []
        all_agents = ['coordinator', 'writer', 'engineer', 'researcher', 'operator', 'evolver', 'community']
        
        for agent in all_agents:
            if agent != from_agent and agent not in exclude:
                self.send_message(from_agent, agent, message)
    
    def update_task_status(self, task_id: str, step: int, status: str, result: Dict = None):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            step: 步骤编号
            status: 状态 (pending/running/completed/failed)
            result: 执行结果
        """
        if task_id not in self.task_status:
            self.task_status[task_id] = {}
        
        self.task_status[task_id][step] = {
            'status': status,
            'result': result,
            'updated_at': datetime.now().isoformat()
        }
        
        print(f"📝 任务 [{task_id}] 步骤 {step}: {status}")
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        return self.task_status.get(task_id, {})
    
    def share_data(self, key: str, data: any, agent: str = None):
        """
        共享数据
        
        Args:
            key: 数据键名
            data: 数据内容
            agent: 共享数据的Agent（可选）
        """
        self.shared_data[key] = {
            'data': data,
            'agent': agent,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"💾 数据共享 [{key}]" + (f" by [{agent}]" if agent else ""))
    
    def get_shared_data(self, key: str) -> Optional[any]:
        """获取共享数据"""
        entry = self.shared_data.get(key)
        return entry['data'] if entry else None


class MultiAgentExecutor:
    """
    多Agent执行器
    
    实际执行多Agent协作任务
    """
    
    def __init__(self):
        self.messenger = AgentMessenger()
        self.agents = {}
    
    def register_agent(self, name: str, handler: Callable):
        """注册Agent处理器"""
        self.agents[name] = handler
    
    def execute_task(self, task_id: str, subtasks: List[Dict]) -> Dict:
        """
        执行多Agent协作任务
        
        Args:
            task_id: 任务ID
            subtasks: 子任务列表
        
        Returns:
            执行结果
        """
        print(f"\n{'='*60}")
        print(f"🚀 开始执行任务: {task_id}")
        print(f"{'='*60}\n")
        
        results = []
        
        for i, subtask in enumerate(subtasks, 1):
            agent_name = subtask['agent']
            action = subtask['action']
            
            print(f"\n📍 步骤 {i}/{len(subtasks)}")
            print(f"   Agent: {agent_name}")
            print(f"   任务: {action}")
            
            # 更新状态为运行中
            self.messenger.update_task_status(task_id, i, 'running')
            
            # 模拟执行（实际应调用Agent处理器）
            # 这里用模拟数据演示
            result = self._simulate_execute(agent_name, action)
            
            # 更新状态为完成
            self.messenger.update_task_status(task_id, i, 'completed', result)
            
            # 共享结果数据
            self.messenger.share_data(f'step_{i}_result', result, agent_name)
            
            results.append({
                'step': i,
                'agent': agent_name,
                'action': action,
                'result': result
            })
            
            # 发送消息给下一个Agent（如果有）
            if i < len(subtasks):
                next_agent = subtasks[i]['agent']
                self.messenger.send_message(
                    agent_name,
                    next_agent,
                    {
                        'type': 'handover',
                        'step': i,
                        'result': result,
                        'message': f'步骤 {i} 完成，请继续执行步骤 {i+1}'
                    }
                )
        
        # 汇总结果
        final_result = self._aggregate_results(results)
        
        print(f"\n{'='*60}")
        print(f"✅ 任务执行完成: {task_id}")
        print(f"{'='*60}\n")
        
        return final_result
    
    def _simulate_execute(self, agent_name: str, action: str) -> Dict:
        """模拟Agent执行（实际应调用真实Agent）"""
        # 这里模拟不同Agent的执行结果
        simulations = {
            'researcher': {
                'status': 'success',
                'data': f'搜索到关于"{action}"的10条相关资料',
                'sources': ['什么值得买', '京东', '天猫']
            },
            'writer': {
                'status': 'success',
                'content': f'已撰写"{action}"文案，字数800字',
                'format': 'markdown'
            },
            'engineer': {
                'status': 'success',
                'code': f'完成"{action}"功能开发',
                'lines': 150
            },
            'operator': {
                'status': 'success',
                'action': f'已执行"{action}"',
                'time': datetime.now().isoformat()
            },
            'evolver': {
                'status': 'success',
                'optimization': f'优化了"{action}"，性能提升20%'
            },
            'community': {
                'status': 'success',
                'interaction': f'完成"{action}"，获得50个互动'
            }
        }
        
        return simulations.get(agent_name, {'status': 'success', 'message': '执行完成'})
    
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """汇总所有步骤的结果"""
        return {
            'total_steps': len(results),
            'completed_steps': len([r for r in results if r['result'].get('status') == 'success']),
            'results': results,
            'summary': f'成功执行 {len(results)} 个步骤，所有Agent协作完成'
        }


# 使用示例
if __name__ == "__main__":
    from coordinator import CoordinatorAgent
    
    # 创建总指挥
    coordinator = CoordinatorAgent()
    
    # 创建执行器
    executor = MultiAgentExecutor()
    
    # 测试任务
    task = "发小红书介绍TGM1N产品"
    
    # 分析并分解任务
    analysis = coordinator.analyze_task(task)
    subtasks = coordinator.decompose_task(analysis)
    
    # 生成任务ID
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 显示调度计划
    print(coordinator.dispatch(subtasks))
    
    # 执行多Agent协作
    result = executor.execute_task(task_id, subtasks)
    
    print("\n📊 执行结果汇总:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
