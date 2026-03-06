#!/usr/bin/env python3
"""
电商运营技能包 - 快速入口
支持标签: #电商
"""

import sys
import re

def parse_ecommerce_query(user_input):
    """
    解析电商相关查询
    
    支持格式:
    - #电商 生成产品图 白色背景 无线耳机
    - #电商 写标题 智能手表
    - #电商 分析竞品 蓝牙耳机
    """
    # 移除标签
    clean_input = re.sub(r'^#电商\s*', '', user_input.strip())
    
    # 分析意图
    if any(kw in clean_input for kw in ['图', '画图', '图片', '生成']):
        return 'image', clean_input
    elif any(kw in clean_input for kw in ['标题', '文案', '描述', '卖点', '详情']):
        return 'seo', clean_input
    elif any(kw in clean_input for kw in ['分析', '研究', '调研', '竞品']):
        return 'research', clean_input
    else:
        return 'general', clean_input

def main():
    if len(sys.argv) > 1:
        user_input = ' '.join(sys.argv[1:])
    else:
        user_input = input("请输入电商查询: ")
    
    intent, query = parse_ecommerce_query(user_input)
    
    print(f"🔍 意图识别: {intent}")
    print(f"🛒 查询内容: {query}")
    print("\n✅ 电商运营技能包已就绪")
    print("可用功能:")
    print("  - 🖼️ AI图片生成: #画图 [描述]")
    print("  - ✍️ SEO Writer: #电商 写标题/文案 [产品]")
    print("  - 🌐 网页搜索: #搜索 [产品] 竞品/趋势")
    print("  - 🔬 深度研究: 深度研究 [行业] 电商市场")

if __name__ == "__main__":
    main()
