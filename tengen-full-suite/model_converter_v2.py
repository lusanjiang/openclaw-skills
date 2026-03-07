#!/usr/bin/env python3
"""
天正物料型号标准化转换器 - 支持乱序输入
"""

import re

def convert_tengen_model(user_input):
    """
    将用户输入的天正型号转换为标准格式
    支持乱序输入，自动识别各部分
    
    输入示例: 
      - 标准顺序: TGB1N 63a 3p c25
      - 乱序: 2P C50 125 tgb1n
      - 混合: tgb1n 125 2p c50
    
    输出: TGB1N-125 2P C50(祥云3.0)
    """
    
    # 清理输入，统一大写
    input_clean = user_input.strip().upper()
    
    # 提取各部分
    # 1. 系列 (TGB1N, TGM1N, TGW1N, TeW等)
    series_match = re.search(r'(T[G|E][A-Z0-9]+)', input_clean)
    series = series_match.group(1) if series_match else None
    
    # 2. 极数 (1P, 2P, 3P, 4P) - 先提取避免混淆
    poles_match = re.search(r'(\d+)P', input_clean)
    poles = poles_match.group(0) if poles_match else None
    
    # 3. 曲线+电流 (C1, C2, D10, C25, C50等) - C/D开头的
    curve_current_match = re.search(r'([C|D])(\d+)', input_clean)
    if curve_current_match:
        curve = curve_current_match.group(1)
        current = curve_current_match.group(2)
        curve_current = f"{curve}{current}"
    else:
        curve_current = None
    
    # 4. 壳架电流 - 剩余的大数字（排除极数和曲线电流中的数字）
    # 找到所有数字
    all_numbers = re.findall(r'\d+', input_clean)
    # 排除极数
    if poles_match:
        pole_num = poles_match.group(1)
        all_numbers = [n for n in all_numbers if n != pole_num]
    # 排除曲线电流
    if curve_current_match:
        curve_num = curve_current_match.group(2)
        all_numbers = [n for n in all_numbers if n != curve_num]
    
    # 壳架通常是剩余数字中较大的（32-6300）
    frame_current = None
    for num in all_numbers:
        n = int(num)
        if n >= 32 and n <= 6300:
            frame_current = num
            break
    
    # 检查是否完整
    if not all([series, frame_current, poles, curve_current]):
        missing = []
        if not series: missing.append("系列")
        if not frame_current: missing.append("壳架电流")
        if not poles: missing.append("极数")
        if not curve_current: missing.append("曲线电流")
        return {
            "success": False,
            "error": f"型号信息不完整，缺少: {', '.join(missing)}"
        }
    
    # 标准格式
    standard_format = f"{series}-{frame_current} {poles} {curve_current}(祥云3.0)"
    
    return {
        "success": True,
        "input": user_input,
        "standard_format": standard_format,
        "parsed": {
            "series": series,
            "frame_current": frame_current,
            "poles": poles,
            "curve_current": curve_current
        }
    }


if __name__ == "__main__":
    # 测试各种输入
    test_cases = [
        "TGB1N 63a 3p c25",      # 标准顺序
        "2P C50 125 tgb1n",      # 乱序
        "tgb1n 125 2p c50",      # 混合顺序
        "TGM1N 100 3P C63",      # 塑壳
        "TGW1N 2000 3P C",       # 框架（缺电流）
    ]
    
    for test in test_cases:
        print(f"\n输入: {test}")
        result = convert_tengen_model(test)
        if result["success"]:
            print(f"✅ 标准格式: {result['standard_format']}")
        else:
            print(f"❌ 错误: {result['error']}")
