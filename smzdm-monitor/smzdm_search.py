#!/usr/bin/env python3
"""
什么值得买监控 - #我想买 Skill
快速查询商品优惠，筛选高价值商品
"""

import requests
import sys


def search_smzdm(keyword):
    """
    搜索什么值得买商品 - 使用搜索API
    
    Args:
        keyword: 搜索关键词
    
    Returns:
        筛选后的商品列表
    """
    # 使用什么值得买搜索API
    url = "https://search.smzdm.com/"
    params = {
        'c': 'home',  # 好价频道
        's': keyword,
        'order': 'time',  # 按时间排序获取最新
        'v': 'a',  # 商品
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        # 解析HTML获取商品信息（这里简化处理，实际应该解析HTML）
        # 由于需要解析HTML，暂时返回模拟数据
        
        # 尝试使用备用API
        api_url = "https://api.smzdm.com/v1/list"
        api_params = {
            'keyword': keyword,
            'channel': 'home',
            'order': 'time',  # 按时间排序
            'limit': 50
        }
        
        resp = requests.get(api_url, params=api_params, headers=headers, timeout=30)
        data = resp.json()
        
        if data.get('error_code') != '0':
            return []
        
        rows = data['data']['rows']
        filtered = []
        
        for item in rows:
            title = item.get('article_title', '')
            price = item.get('article_price', '')
            link = item.get('article_url', '')
            comment = int(item.get('article_comment', 0))
            worthy = int(item.get('article_worthy', 0))
            unworthy = int(item.get('article_unworthy', 0))
            date = item.get('article_date', '')
            
            # 跳过过期的
            if '过期' in price or '过期' in title or '已售罄' in price:
                continue
            
            # 跳过社区文章（没有价格或价格字段包含#）
            if not price or price.startswith('#') or '元' not in price:
                continue
            
            # 计算值率
            total = worthy + unworthy
            worth_pct = (worthy/total*100) if total > 0 else 0
            
            # 筛选条件：评论>10，值>85%
            if comment > 10 and worth_pct > 85:
                filtered.append({
                    'title': title,
                    'price': price,
                    'comment': comment,
                    'worth_pct': worth_pct,
                    'link': link,
                    'date': date
                })
        
        return filtered
    
    except Exception as e:
        print(f"请求失败: {e}")
        return []


def print_results(keyword, items):
    """打印结果"""
    print(f"🔍 搜索：{keyword}")
    print()
    
    if not items:
        print("❌ 暂无符合条件的商品")
        print("筛选条件：评论>10条，值>85%，未过期")
        return
    
    print(f"✅ 找到 {len(items)} 条有效商品：\n")
    print("| 排名 | 商品名称 | 价格 | 评论 | 值率 | 链接 |")
    print("|:---|:---|:---|:---:|:---:|:---|")
    
    for i, item in enumerate(items[:10], 1):
        title_short = item['title'][:30] + "..." if len(item['title']) > 30 else item['title']
        print(f"| {i} | {title_short} | {item['price']} | {item['comment']}条 | {item['worth_pct']:.1f}% | [查看]({item['link']}) |")
    
    print()


if __name__ == "__main__":
    # 获取关键词
    if len(sys.argv) > 1:
        keyword = ' '.join(sys.argv[1:])
    else:
        keyword = "燃气热水器"  # 默认关键词
    
    # 搜索并输出
    items = search_smzdm(keyword)
    print_results(keyword, items)
