#!/usr/bin/env python3
"""
天正电气证书智能查询 Skill
自动解析用户查询，按"证书类型 + 系列"格式搜索
"""

import requests
import re
import sys


def parse_query(user_input):
    """
    解析用户查询，提取证书类型、产品系列和文档类型

    支持格式：
    - "TGB1N-63 的 CCC证书" → (CCC, TGB1N-63, '证书')
    - "帮我找TGM1N的3C报告" → (3C, TGM1N, '报告')
    - "TGW1N型式试验" → (型式试验, TGW1N, None)
    """
    # 证书类型关键词
    cert_types = {
        'CCC': ['CCC', '3C', 'ccc', '3c'],
        'CQC': ['CQC', 'cqc'],
        'CE': ['CE', 'ce', 'CE认证'],
        'CB': ['CB', 'cb'],
        '型式试验': ['型式试验', '试验报告', '检测报告'],
        'UL': ['UL', 'ul'],
        'TUV': ['TUV', 'tuv'],
        'RoHS': ['RoHS', 'rohs', 'ROHS'],
        'ISO': ['ISO', 'iso']
    }

    # 产品系列匹配模式
    series_patterns = [
        r'TG[A-Z]\d+[A-Z]?-?\d*',   # TGB1N-63, TGM1N-400, TGW1N-2000
        r'TG[A-Z][A-Z]?-?\d*',       # TGBG-63, TGBH-63, TGH-63 (连续字母)
    ]

    # 查找证书类型
    cert_type = None
    for cert_key, keywords in cert_types.items():
        for kw in keywords:
            if kw in user_input.upper() or kw in user_input:
                cert_type = cert_key
                break
        if cert_type:
            break

    # 默认证书类型
    if not cert_type:
        cert_type = 'CCC'

    # 查找文档类型（证书 vs 报告）- 新增
    doc_type = None
    if '证书' in user_input or '认证' in user_input:
        doc_type = '证书'
    elif '报告' in user_input:
        doc_type = '报告'

    # 查找产品系列
    product_series = None
    for pattern in series_patterns:
        match = re.search(pattern, user_input.upper())
        if match:
            product_series = match.group()
            break

    return cert_type, product_series, doc_type


def build_search_query(cert_type, product_series):
    """
    构建搜索查询字符串
    格式: "证书类型 产品系列"
    例如: "CCC TGB1N-63"
    """
    if product_series:
        return f"{cert_type} {product_series}"
    return cert_type


def search_certificates(query, exact_model=None, doc_type=None):
    """
    查询天正官网证书
    exact_model: 如果指定，只返回精确匹配该型号的结果
    doc_type: 如果指定'证书'或'报告'，只返回对应类型的结果
    """
    url = "https://www.tengen.com/api/Order/getFileux"

    cookies = {
        "accessId": "4208aa20-a416-11e8-ba0f-1960c9d1906b",
        "pageViewNum": "1"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    results = []

    # 搜索前5页
    for page in range(1, 6):
        post_data = {
            "sample": "",
            "product1": "",
            "product2": "",
            "userinput": query,
            "uxpage": str(page)
        }

        try:
            response = requests.post(url, data=post_data, cookies=cookies,
                                    headers=headers, timeout=10)
            response.raise_for_status()
            json_data = response.json()

            if "data" in json_data and json_data["data"]:
                for item in json_data["data"]:
                    if "file" in item and "title" in item:
                        file_url = "https://www.tengen.com" + item["file"]
                        title = item["title"]

                        # 如果指定了精确型号，过滤掉不精确匹配的
                        if exact_model and not is_exact_model_match(title, exact_model):
                            continue

                        # 如果指定了文档类型（证书/报告），进行过滤
                        if doc_type == '证书' and '证书' not in title and '认证' not in title:
                            continue
                        if doc_type == '报告' and '报告' not in title:
                            continue

                        results.append({
                            'title': title,
                            'url': file_url,
                            'relevance': calculate_relevance(title, query)
                        })
        except Exception as e:
            continue

    # 按相关度排序
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results


def calculate_relevance(title, query):
    """
    计算标题与查询的相关度
    精确匹配型号，避免匹配到类似型号（如TGB1N-63不会匹配TGB1N-63DC）
    """
    relevance = 0
    query_parts = query.upper().split()
    title_upper = title.upper()

    for part in query_parts:
        if part in title_upper:
            relevance += 10
        # 部分匹配
        elif len(part) > 3 and part[:4] in title_upper:
            relevance += 5

    return relevance


def is_exact_model_match(title, model):
    """
    检查标题中是否包含精确匹配的型号
    例如：TGB1N-63 不会匹配 TGB1N-63DC 或 TGB1N-63S
    """
    if not model:
        return True

    title_upper = title.upper()
    model_upper = model.upper()

    # 查找型号在标题中的位置
    idx = title_upper.find(model_upper)
    if idx == -1:
        return False

    # 检查型号后面是否紧跟着字母或数字（即是否为精确匹配）
    # TGB1N-63 后面应该是空格、逗号、顿号、括号或字符串结尾
    end_pos = idx + len(model_upper)
    if end_pos < len(title_upper):
        next_char = title_upper[end_pos]
        # 如果后面紧跟的是字母或数字，说明是其他型号（如TGB1N-63DC）
        if next_char.isalnum():
            return False

    return True


def format_results(results, query, exact_model=None, doc_type=None, max_results=5):
    """
    格式化输出结果 - 便于复制链接到微信
    """
    if not results:
        msg = f"❌ 未找到与「{query}」相关的证书"
        if exact_model:
            msg += f"\n   (已过滤，只显示精确匹配「{exact_model}」的证书)"
        if doc_type:
            msg += f"\n   (已过滤，只显示「{doc_type}」类型)"
        return msg

    output = f"🔍 查询: {query}\n"
    if exact_model:
        output += f"📋 精确匹配型号: {exact_model}（已过滤其他型号如{exact_model}DC、{exact_model}S等）\n"
    if doc_type:
        output += f"📄 文档类型: {doc_type}（已过滤其他类型）\n"
    output += f"✅ 找到 {len(results)} 个结果:\n\n"

    for i, item in enumerate(results[:max_results], 1):
        output += f"【{i}】{item['title']}\n"
        output += f"    下载链接:\n"
        output += f"    {item['url']}\n\n"

    return output


def main():
    # 获取用户输入
    if len(sys.argv) > 1:
        user_input = ' '.join(sys.argv[1:])
    else:
        user_input = input("请输入查询内容: ")

    # 解析查询
    cert_type, product_series, doc_type = parse_query(user_input)

    # 构建搜索查询
    search_query = build_search_query(cert_type, product_series)

    # 执行搜索（传入精确型号和文档类型进行过滤）
    results = search_certificates(search_query, exact_model=product_series, doc_type=doc_type)

    # 输出结果
    print(format_results(results, search_query, exact_model=product_series, doc_type=doc_type))


if __name__ == "__main__":
    main()
