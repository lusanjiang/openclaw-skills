#!/usr/bin/env python3
"""
华为FreeClip耳夹式耳机专用监控
检测到好价才推送提醒
"""

import requests
import time
from datetime import datetime


class FreeClipMonitor:
    """华为FreeClip专用监控器"""
    
    def __init__(self):
        self.api_url = "https://api.smzdm.com/v1/list"
        self.target_keywords = ['华为FreeClip', 'FreeClip', '华为耳夹', '耳夹式耳机']
        self.seen_ids = set()
        
    def search_freeclip(self):
        """搜索华为FreeClip"""
        all_items = []
        
        for keyword in self.target_keywords:
            params = {
                'keyword': keyword,
                'channel': 'home',
                'order': 'hot',
                'limit': 50
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                resp = requests.get(self.api_url, params=params, headers=headers, timeout=30)
                data = resp.json()
                
                if data.get('error_code') == '0':
                    all_items.extend(data['data']['rows'])
            except:
                continue
        
        return all_items
    
    def filter_freeclip(self, items):
        """筛选华为FreeClip好价"""
        filtered = []
        
        for item in items:
            article_id = item.get('article_id', '')
            
            # 跳过已处理的
            if article_id in self.seen_ids:
                continue
            
            title = item.get('article_title', '')
            price_str = item.get('article_price', '')
            link = item.get('article_url', '')
            comment = int(item.get('article_comment', 0))
            worthy = int(item.get('article_worthy', 0))
            unworthy = int(item.get('article_unworthy', 0))
            
            # 检查是否包含FreeClip
            title_lower = title.lower()
            title_upper = title.upper()
            if 'freeclip' not in title_lower and '耳夹' not in title_lower:
                continue
            if '华为' not in title and 'HUAWEI' not in title_upper:
                continue
            
            # 跳过过期的
            if '过期' in price_str or '已售罄' in price_str:
                continue
            
            # 提取价格数字
            import re
            price_match = re.search(r'(\d+\.?\d*)', price_str)
            price = float(price_match.group(1)) if price_match else 0
            
            # 计算值率
            total = worthy + unworthy
            worth_pct = (worthy/total*100) if total > 0 else 0
            
            # 好价条件：价格<1000元，评论>5条，值>80%
            if price > 0 and price < 1000 and comment > 5 and worth_pct > 80:
                deal = {
                    'id': article_id,
                    'title': title,
                    'price': price_str,
                    'price_num': price,
                    'link': link,
                    'comment': comment,
                    'worthy': worthy,
                    'unworthy': unworthy,
                    'worth_pct': round(worth_pct, 1),
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                filtered.append(deal)
                self.seen_ids.add(article_id)
        
        return filtered
    
    def check_once(self):
        """执行一次检查"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在监控华为FreeClip...")
        
        items = self.search_freeclip()
        if not items:
            return []
        
        good_deals = self.filter_freeclip(items)
        
        if good_deals:
            print(f"\n🎉 检测到 {len(good_deals)} 条华为FreeClip好价！\n")
            for deal in good_deals:
                print(f"🔥 {deal['title']}")
                print(f"   💰 {deal['price']}")
                print(f"   💬 {deal['comment']}条评论")
                print(f"   📊 {deal['worth_pct']}%值率")
                print(f"   🔗 {deal['link']}")
                print()
        else:
            print("暂无好价（价格<1000元，评论>5条，值>80%）")
        
        return good_deals
    
    def run_continuous(self, interval=600):
        """
        持续监控
        
        Args:
            interval: 检查间隔（秒），默认10分钟
        """
        print("=" * 60)
        print("华为FreeClip耳夹式耳机 - 好价监控")
        print("=" * 60)
        print("监控条件：价格<1000元，评论>5条，值>80%")
        print(f"检查间隔：{interval}秒")
        print("=" * 60)
        print()
        
        try:
            while True:
                deals = self.check_once()
                
                if deals:
                    print("⚡ 发现好价！已推送提醒")
                else:
                    print(f"⏳ 暂无好价，{interval}秒后再次检查...")
                
                print()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n监控已停止")


if __name__ == "__main__":
    monitor = FreeClipMonitor()
    
    # 单次检查
    monitor.check_once()
    
    # 持续监控（取消注释以启用）
    # monitor.run_continuous(interval=600)
