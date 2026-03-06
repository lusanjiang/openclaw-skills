#!/usr/bin/env python3
"""
天正电气证书查询 - 标签触发入口
支持 #查询证书 标签快速调用
"""

import sys
import os

# 添加技能目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cert_query import main as cert_query_main

if __name__ == "__main__":
    # 标签触发时，从命令行参数获取查询内容
    if len(sys.argv) > 1:
        # 去掉 #查询证书 标签本身
        query = ' '.join(sys.argv[1:])
        # 重新设置参数并调用主函数
        sys.argv = [sys.argv[0]] + sys.argv[1:]
        cert_query_main()
    else:
        print("使用方法: #查询证书 [产品型号] 的 [证书类型]")
        print("示例: #查询证书 TGB1N-63的CCC证书")
