#!/usr/bin/env python3
"""
总指挥调度系统 - Coordinator Agent
自动分解复杂任务，调度各专业Agent执行
"""

import json
import re
from typing import List, Dict, Optional
from datetime import datetime


class CoordinatorAgent:
    """
    总指挥Agent
    
    职责：
    1. 接收用户任务
    2. 分析任务类型
    3. 分解为子任务
    4. 调度专业Agent
    5. 整合结果输出
    """
    
    # Agent技能映射
    AGENT_SKILLS = {
        'writer': {
            'name': '笔杆子',
            'skills': ['写作', '文案', '报告', '小红书', '文档'],
            'tag': '#写作'
        },
        'engineer': {
            'name': '工程师',
            'skills': ['开发', '代码', '爬虫', 'API', '工具', '脚本'],
            'tag': '#开发'
        },
        'researcher': {
            'name': '情报官',
            'skills': ['搜索', '调研', '分析', '数据', '信息'],
            'tag': '#调研'
        },
        'operator': {
            'name': '运营官',
            'skills': ['定时', '监控', '维护', '备份', '巡检'],
            'tag': '#运营'
        },
        'evolver': {
            'name': '进化官',
            'skills': ['学习', '优化', '反思', '升级', '改进'],
            'tag': '#进化'
        },
        'community': {
            'name': '社区官',
            'skills': ['互动', '回复', '消息', '关系', '彩蛋'],
            'tag': '#互动'
        }
    }
    
    def __init__(self):
        self.task_history = []
        self.current_task = None
    
    def analyze_task(self, user_input: str) -> Dict:
        """
        分析用户任务类型
        
        Returns:
            任务分析结果
        """
        user_input_lower = user_input.lower()
        
        # 关键词匹配
        keywords = {
            'writer': ['写', '文案', '报告', '小红书', '文档', '内容', '文章'],
            'engineer': ['开发', '代码', '爬虫', 'API', '工具', '脚本', '程序'],
            'researcher': ['搜索', '调研', '查', '找', '分析', '数据', '信息'],
            'operator': ['定时', '监控', '维护', '备份', '巡检', '自动'],
            'evolver': ['学习', '优化', '改进', '升级', '反思', '进化'],
            'community': ['回复', '互动', '消息', '彩蛋', '关系']
        }
        
        scores = {}
        for agent, words in keywords.items():
            score = sum(1 for w in words if w in user_input_lower)
            scores[agent] = score
        
        # 找出最匹配的Agent
        best_agent = max(scores, key=scores.get)
        
        # 判断是否需要多Agent协作
        complexity = self._assess_complexity(user_input)
        
        return {
            'input': user_input,
            'primary_agent': best_agent,
            'agent_name': self.AGENT_SKILLS[best_agent]['name'],
            'tag': self.AGENT_SKILLS[best_agent]['tag'],
            'complexity': complexity,
            'scores': scores
        }
    
    def _assess_complexity(self, task: str) -> str:
        """评估任务复杂度"""
        # 复杂任务指示词
        complex_indicators = [
            '然后', '再', '同时', '并且', '最后', '先', '分步骤',
            '包括', '以及', '和', '先...再', '第一步', '第二步',
            '完整', '系统', '全流程', '端到端'
        ]
        
        # 如果包含多个动词或步骤词，认为是复杂任务
        action_words = ['搜索', '写', '开发', '整理', '发', '分析', '生成', '处理']
        action_count = sum(1 for word in action_words if word in task)
        
        if any(ind in task for ind in complex_indicators) or action_count >= 2:
            return 'complex'
        elif len(task) > 50 or action_count >= 1:
            return 'medium'
        else:
            return 'simple'
    
    def decompose_task(self, analysis: Dict) -> List[Dict]:
        """
        分解任务为子任务
        
        Args:
            analysis: 任务分析结果
        
        Returns:
            子任务列表
        """
        subtasks = []
        
        if analysis['complexity'] == 'simple':
            # 简单任务，直接分配
            subtasks.append({
                'step': 1,
                'agent': analysis['primary_agent'],
                'action': analysis['input'],
                'status': 'pending'
            })
        else:
            # 复杂任务，需要分解
            # 这里可以根据具体任务类型定制分解逻辑
            subtasks = self._custom_decompose(analysis)
        
        return subtasks
    
    def _custom_decompose(self, analysis: Dict) -> List[Dict]:
        """根据任务类型定制分解"""
        input_text = analysis['input']
        subtasks = []
        
        # 示例：发布小红书笔记
        if '小红书' in input_text and ('发' in input_text or '写' in input_text):
            subtasks = [
                {'step': 1, 'agent': 'researcher', 'action': '搜索相关资料', 'status': 'pending'},
                {'step': 2, 'agent': 'writer', 'action': '撰写文案', 'status': 'pending'},
                {'step': 3, 'agent': 'engineer', 'action': '生成/处理图片', 'status': 'pending'},
                {'step': 4, 'agent': 'operator', 'action': '发布笔记', 'status': 'pending'}
            ]
        # 示例：研究+报告+发布
        elif '研究' in input_text and ('报告' in input_text or '整理' in input_text) and ('发' in input_text or '发布' in input_text):
            subtasks = [
                {'step': 1, 'agent': 'researcher', 'action': '搜索相关资料和数据', 'status': 'pending'},
                {'step': 2, 'agent': 'writer', 'action': '整理并撰写报告', 'status': 'pending'},
                {'step': 3, 'agent': 'community', 'action': '发布到目标平台', 'status': 'pending'}
            ]
        # 示例：开发完整系统
        elif ('开发' in input_text or '系统' in input_text) and ('完整' in input_text or '包括' in input_text):
            subtasks = [
                {'step': 1, 'agent': 'researcher', 'action': '调研需求和技术方案', 'status': 'pending'},
                {'step': 2, 'agent': 'engineer', 'action': '开发核心功能模块', 'status': 'pending'},
                {'step': 3, 'agent': 'writer', 'action': '编写文档和使用说明', 'status': 'pending'},
                {'step': 4, 'agent': 'evolver', 'action': '测试、优化和部署', 'status': 'pending'}
            ]
        else:
            # 默认分解
            subtasks.append({
                'step': 1,
                'agent': analysis['primary_agent'],
                'action': analysis['input'],
                'status': 'pending'
            })
        
        return subtasks
    
    def dispatch(self, subtasks: List[Dict]) -> str:
        """
        调度Agent执行任务
        
        Returns:
            调度计划文本
        """
        output = []
        output.append("=" * 50)
        output.append("🎯 总指挥任务调度")
        output.append("=" * 50)
        output.append("")
        
        for task in subtasks:
            agent_key = task['agent']
            agent_info = self.AGENT_SKILLS[agent_key]
            
            output.append(f"步骤 {task['step']}:")
            output.append(f"  👤 Agent: {agent_info['name']} ({agent_key})")
            output.append(f"  🏷️  标签: {agent_info['tag']}")
            output.append(f"  📝 任务: {task['action']}")
            output.append(f"  ⏳ 状态: {task['status']}")
            output.append("")
        
        output.append("=" * 50)
        output.append("调度完成，开始执行...")
        
        return "\n".join(output)
    
    def process(self, user_input: str) -> str:
        """
        处理用户输入的完整流程
        
        Args:
            user_input: 用户输入
        
        Returns:
            处理结果
        """
        # 1. 分析任务
        analysis = self.analyze_task(user_input)
        
        # 2. 分解任务
        subtasks = self.decompose_task(analysis)
        
        # 3. 调度执行
        plan = self.dispatch(subtasks)
        
        # 4. 记录历史
        self.task_history.append({
            'time': datetime.now().isoformat(),
            'input': user_input,
            'analysis': analysis,
            'subtasks': subtasks
        })
        
        return plan


# 使用示例
if __name__ == "__main__":
    coordinator = CoordinatorAgent()
    
    # 测试任务
    test_tasks = [
        "发小红书介绍TGM1N",
        "开发一个燃气热水器价格监控工具",
        "搜索天正电气最新新闻",
        "定时备份我的数据"
    ]
    
    for task in test_tasks:
        print(f"\n{'='*50}")
        print(f"用户输入: {task}")
        print('='*50)
        result = coordinator.process(task)
        print(result)
        print()
