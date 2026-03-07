#!/usr/bin/env python3
"""
天正物料型号标准化转换器
"""

def convert_tengen_model(user_input):
    """
    将用户输入的天正型号转换为标准格式
    
    输入示例: TGB1N 63a 3p c25
    输出: TGB1N-63 3P C25(祥云3.0)
    """
    
    # 清理输入
    input_clean = user_input.strip().upper()
    
    # 解析各部分
    import re
    
    # 匹配模式: TGB1N [壳架] [极数] [曲线电流]
    # 示例: TGB1N 63A 3P C25
    
    parts = input_clean.split()
    
    if len(parts) < 4:
        return {"success": False, "error": "型号格式不完整"}
    
    # 第一部分: 系列+壳架 (如 TGB1N-63 或 TGB1N)
    series = parts[0]
    
    # 第二部分: 壳架电流 (如 63A)
    frame_current = parts[1].replace('A', '').replace('a', '')
    
    # 第三部分: 极数 (如 3P)
    poles = parts[2].replace('P', 'P').replace('p', 'P')
    
    # 第四部分: 曲线+电流 (如 C25)
    curve_current = parts[3]
    
    # 标准格式（物料编码）
    # TGB1N-63 3P C25(祥云3.0)
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
    # 测试
    test_input = "TGB1N 63a 3p c25"
    result = convert_tengen_model(test_input)
    
    if result["success"]:
        print(f"✅ 型号识别成功！")
        print(f"输入: {result['input']}")
        print(f"标准格式: {result['standard_format']}")
        print(f"物料编码: {result['material_code']}")
    else:
        print(f"❌ 错误: {result['error']}")
