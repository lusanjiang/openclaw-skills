#!/usr/bin/env python3
"""
股票分析师技能包 - 快速入口
支持标签: #股票
"""

import sys
import re

def parse_stock_query(user_input):
    """
    解析股票相关查询
    
    支持格式:
    - #股票 分析 宁德时代
    - #股票 查 贵州茅台
    - #股票 研究 新能源行业
    """
    # 移除标签
    clean_input = re.sub(r'^#股票\s*', '', user_input.strip())
    
    # 分析意图
    if any(kw in clean_input for kw in ['分析', '研究', '调研']):
        return 'research', clean_input
    elif any(kw in clean_input for kw in ['查', '搜索', '找']):
        return 'search', clean_input
    elif any(kw in clean_input for kw in ['计算', '算', '收益']):
        return 'calculate', clean_input
    else:
        return 'analysis', clean_input

def main():
    if len(sys.argv) > 1:
        user_input = ' '.join(sys.argv[1:])
    else:
        user_input = input("请输入股票查询: ")
    
    intent, query = parse_stock_query(user_input)
    
    print(f"🔍 意图识别: {intent}")
    print(f"📊 查询内容: {query}")
    print("\n✅ 股票分析师技能包已就绪")
    print("可用功能:")
    print("  - 🌐 网页搜索: #搜索 [股票名称] [关键词]")
    print("  - 🔬 深度研究: 深度研究 [股票/行业] [主题]")
    print("  - 💻 代码助手: 帮我写个 [策略] 的Python代码")
    print("  - 🧠 智能计算: 计算 [股票数据]")

if __name__ == "__main__":
    main()
