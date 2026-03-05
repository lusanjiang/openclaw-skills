#!/usr/bin/env python3
"""
GitHub高星标Skill自动检索学习系统
每30分钟自动检索并学习新技能
"""

import requests
import json
import time
from datetime import datetime


class GitHubSkillLearner:
    """
    GitHub Skill自动学习器
    """
    
    def __init__(self):
        self.github_api = "https://api.github.com"
        self.learned_skills = set()  # 已学习的技能
        self.skill_keywords = [
            'openclaw skill',
            'clawbot skill', 
            'ai agent skill',
            'lobster skill',
            'automation skill'
        ]
    
    def search_skills(self) -> list:
        """
        搜索GitHub上的高星标Skill
        
        Returns:
            技能列表
        """
        skills = []
        
        for keyword in self.skill_keywords:
            try:
                # 搜索仓库
                url = f"{self.github_api}/search/repositories"
                params = {
                    'q': f'{keyword} stars:>10',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 10
                }
                
                response = requests.get(url, timeout=30)
                data = response.json()
                
                for item in data.get('items', []):
                    skill = {
                        'name': item['name'],
                        'full_name': item['full_name'],
                        'description': item['description'],
                        'stars': item['stargazers_count'],
                        'url': item['html_url'],
                        'language': item['language'],
                        'updated': item['updated_at']
                    }
                    
                    # 去重
                    if skill['full_name'] not in self.learned_skills:
                        skills.append(skill)
                        
            except Exception as e:
                print(f"搜索失败 {keyword}: {e}")
                continue
        
        # 按星标排序
        skills.sort(key=lambda x: x['stars'], reverse=True)
        return skills[:5]  # 取前5个
    
    def learn_skill(self, skill: dict) -> dict:
        """
        学习技能
        
        Args:
            skill: 技能信息
        
        Returns:
            学习结果
        """
        print(f"\n📚 正在学习技能: {skill['name']}")
        print(f"   ⭐ 星标: {skill['stars']}")
        print(f"   📝 描述: {skill['description']}")
        
        try:
            # 获取README内容
            readme_url = f"{self.github_api}/repos/{skill['full_name']}/readme"
            response = requests.get(readme_url, timeout=30)
            
            if response.status_code == 200:
                readme_data = response.json()
                import base64
                content = base64.b64decode(readme_data['content']).decode('utf-8')
                
                # 提取关键信息
                summary = self._extract_summary(content)
                
                # 标记为已学习
                self.learned_skills.add(skill['full_name'])
                
                return {
                    'status': 'success',
                    'skill': skill,
                    'summary': summary,
                    'learned_at': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'skill': skill,
                    'error': '无法获取README'
                }
                
        except Exception as e:
            return {
                'status': 'error', 
                'skill': skill,
                'error': str(e)
            }
    
    def _extract_summary(self, readme: str) -> str:
        """从README提取关键信息"""
        lines = readme.split('\n')
        summary = []
        
        for line in lines[:20]:  # 取前20行
            if line.strip() and not line.startswith('#'):
                summary.append(line.strip())
            if len(summary) >= 3:
                break
        
        return ' '.join(summary)[:200]
    
    def run_learning_cycle(self):
        """执行学习周期"""
        print(f"\n{'='*60}")
        print(f"🔍 GitHub Skill自动学习 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 搜索技能
        skills = self.search_skills()
        
        if not skills:
            print("未发现新技能")
            return
        
        print(f"发现 {len(skills)} 个新技能\n")
        
        # 学习每个技能
        results = []
        for skill in skills:
            result = self.learn_skill(skill)
            results.append(result)
            
            if result['status'] == 'success':
                print(f"   ✅ 学习完成")
            else:
                print(f"   ❌ 学习失败: {result.get('error', '未知错误')}")
            
            time.sleep(2)  # 避免请求过快
        
        # 生成学习报告
        self._generate_report(results)
    
    def _generate_report(self, results: list):
        """生成学习报告"""
        success_count = len([r for r in results if r['status'] == 'success'])
        
        print(f"\n{'='*60}")
        print(f"📊 学习报告")
        print(f"{'='*60}")
        print(f"总计: {len(results)} 个技能")
        print(f"成功: {success_count} 个")
        print(f"失败: {len(results) - success_count} 个")
        print(f"{'='*60}\n")
        
        # 保存学习记录
        report = {
            'timestamp': datetime.now().isoformat(),
            'total': len(results),
            'success': success_count,
            'results': results
        }
        
        with open('/tmp/github_skill_learning.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def run_continuous(self, interval=1800):
        """
        持续运行
        
        Args:
            interval: 检查间隔（秒），默认30分钟
        """
        print(f"🚀 GitHub Skill自动学习系统启动")
        print(f"⏰ 检查间隔: {interval/60} 分钟\n")
        
        try:
            while True:
                self.run_learning_cycle()
                print(f"\n⏳ 等待 {interval/60} 分钟后下次检查...\n")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n系统已停止")


# 使用示例
if __name__ == "__main__":
    learner = GitHubSkillLearner()
    
    # 单次执行
    learner.run_learning_cycle()
    
    # 持续运行（取消注释以启用）
    # learner.run_continuous(interval=1800)
