#!/usr/bin/env python3
"""
TEMPLAR-003458 基金量化分析 Skill
基于完整1年数据深度回测
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class FundAnalyzer:
    """基金量化分析器"""
    
    def __init__(self, fund_code="017612"):
        self.fund_code = fund_code
        self.data = None
        self.df = None
        
    def fetch_data(self, start_date="2025-03-07", end_date="2026-03-07"):
        """获取基金历史数据"""
        cookies = {
            'st_si': '50620618582032',
            'st_pvi': '63127800375728',
            'st_sp': '2026-03-07%2022%3A36%3A55',
            'st_asi': 'delete',
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'http://fundf10.eastmoney.com/',
        }
        
        params = {
            'type': '0',
            'fundCode': self.fund_code,
            'pageIndex': '1',
            'pageSize': '400',
            'startDate': start_date,
            'endDate': end_date,
        }
        
        try:
            response = requests.get(
                'https://api.fund.eastmoney.com/f10/LSJZChart',
                params=params, cookies=cookies, headers=headers,
                timeout=30
            )
            
            # 解析数据 - 处理可能的JSONP格式
            text = response.text
            # 找到第一个(和最后一个)
            start = text.find('(')
            end = text.rfind(')')
            if start == -1 or end == -1 or start >= end:
                print(f"❌ 无法解析响应格式")
                return None
            json_str = text[start+1:end]
            # 清理可能的换行符
            json_str = json_str.strip()
            data = json.loads(json_str)
            
            if 'Data' in data and data['Data']:
                return data['Data']
            return None
        except Exception as e:
            print(f"❌ 数据获取失败: {e}")
            return None
    
    def parse_data(self, raw_data):
        """解析原始数据"""
        parsed = []
        for item in raw_data:
            if isinstance(item, list) and len(item) >= 4:
                timestamp = float(item[0]) / 1000
                date = datetime.fromtimestamp(timestamp)
                
                parsed.append({
                    'date': date,
                    'date_str': date.strftime('%Y-%m-%d'),
                    'nav': float(item[1]),
                    'accum_nav': float(item[2]),
                    'change': float(item[3]),
                    'weekday': date.weekday(),
                    'is_friday': date.weekday() == 4,
                    'is_monday': date.weekday() == 0,
                    'month': date.month,
                    'year_month': date.strftime('%Y-%m')
                })
        
        self.df = pd.DataFrame(parsed)
        self.df = self.df.sort_values('date').reset_index(drop=True)
        return self.df
    
    def friday_effect_analysis(self):
        """周五效应分析"""
        fridays = self.df[self.df['is_friday'] == True]
        total = len(fridays)
        
        if total == 0:
            return None
        
        up = len(fridays[fridays['change'] > 0])
        down = len(fridays[fridays['change'] < 0])
        down_prob = down / total
        
        return {
            'total_fridays': total,
            'up_count': up,
            'down_count': down,
            'down_probability': down_prob,
            'avg_change': fridays['change'].mean(),
            'max_up': fridays['change'].max(),
            'max_down': fridays['change'].min(),
            'verified': down_prob > 0.6
        }
    
    def rolling_backtest(self, window=4):
        """滚动预测回测"""
        fridays = self.df[self.df['is_friday'] == True].reset_index(drop=True)
        
        if len(fridays) <= window:
            return None
        
        results = []
        for i in range(window, len(fridays)):
            hist = fridays.iloc[i-window:i]
            down_count = len(hist[hist['change'] < 0])
            prob = down_count / window
            
            predicted = '跌' if prob >= 0.5 else '非跌'
            actual = '跌' if fridays.iloc[i]['change'] < 0 else '非跌'
            
            results.append({
                'date': fridays.iloc[i]['date_str'],
                'prob': f"{prob*100:.0f}%",
                'predicted': predicted,
                'actual': actual,
                'change': fridays.iloc[i]['change'],
                'correct': predicted == actual
            })
        
        accuracy = sum(r['correct'] for r in results) / len(results)
        return {
            'accuracy': accuracy,
            'total': len(results),
            'correct': sum(r['correct'] for r in results),
            'details': results[-10:]  # 最近10次
        }
    
    def weekday_pattern(self):
        """周内规律分析"""
        patterns = []
        weekdays = ['周一', '周二', '周三', '周四', '周五']
        
        for i, name in enumerate(weekdays):
            day_data = self.df[self.df['weekday'] == i]
            if len(day_data) > 0:
                up_prob = len(day_data[day_data['change'] > 0]) / len(day_data)
                patterns.append({
                    'day': name,
                    'count': len(day_data),
                    'up_probability': up_prob,
                    'avg_change': day_data['change'].mean(),
                    'volatility': day_data['change'].std()
                })
        
        return patterns
    
    def generate_strategy(self):
        """生成交易策略"""
        friday_stats = self.friday_effect_analysis()
        patterns = self.weekday_pattern()
        
        strategy = {
            'fund_code': self.fund_code,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'data_count': len(self.df),
            'friday_effect': friday_stats,
            'weekday_patterns': patterns,
            'rules': {
                'monday': '加仓' if patterns[0]['up_probability'] > 0.5 else '观望',
                'tuesday': '持有' if patterns[1]['up_probability'] > 0.5 else '观望',
                'wednesday': '减仓' if patterns[2]['up_probability'] < 0.5 else '观望',
                'thursday': '观望',
                'friday': '清仓' if friday_stats['down_probability'] > 0.6 else '观望'
            }
        }
        
        return strategy
    
    def full_analysis(self):
        """执行完整分析"""
        print("="*70)
        print(f"TEMPLAR-003458 基金量化分析 - {self.fund_code}")
        print("="*70)
        
        # 获取数据
        print("\n1. 获取数据...")
        raw = self.fetch_data()
        if not raw:
            return None
        
        self.parse_data(raw)
        print(f"   ✓ 获取到 {len(self.df)} 条数据")
        
        # 周五效应
        print("\n2. 周五效应分析...")
        friday = self.friday_effect_analysis()
        if friday:
            print(f"   周五总数: {friday['total_fridays']}")
            print(f"   下跌概率: {friday['down_probability']*100:.1f}%")
            print(f"   验证结果: {'✅ 通过' if friday['verified'] else '❌ 未通过'}")
        
        # 滚动回测
        print("\n3. 滚动预测回测...")
        backtest = self.rolling_backtest()
        if backtest:
            print(f"   预测准确率: {backtest['accuracy']*100:.1f}%")
            print(f"   ({backtest['correct']}/{backtest['total']})")
        
        # 周内规律
        print("\n4. 周内规律分析...")
        patterns = self.weekday_pattern()
        for p in patterns:
            print(f"   {p['day']}: 上涨概率{p['up_probability']*100:.1f}%, 平均{p['avg_change']:+.2f}%")
        
        # 生成策略
        print("\n5. 生成交易策略...")
        strategy = self.generate_strategy()
        print(f"   周一: {strategy['rules']['monday']}")
        print(f"   周三: {strategy['rules']['wednesday']}")
        print(f"   周五: {strategy['rules']['friday']}")
        
        return strategy


def main():
    """主入口"""
    analyzer = FundAnalyzer("017612")
    result = analyzer.full_analysis()
    
    if result:
        # 保存结果
        with open('/root/.openclaw/workspace/fund_analysis_result.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print("\n✓ 分析结果已保存")


if __name__ == "__main__":
    main()
