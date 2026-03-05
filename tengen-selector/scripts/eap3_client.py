#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天正电气EAP3系统物料查询客户端
用于TGW1N系列断路器选型价格查询
"""

import requests
import json
import time
from typing import List, Dict, Optional


class TengenEAP3Client:
    """天正电气EAP3系统客户端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        })
        self.sid: Optional[str] = None
        self.token: Optional[str] = None
        self.base_url = "https://eap3.tengen.com.cn"
        
    def login(self) -> bool:
        """登录EAP3系统"""
        url = f"{self.base_url}/r/w"
        
        post_data = {
            'userid': 'lusanjiang',
            'pwd': '345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39',
            'cmd': 'com.actionsoft.apps.tengen.login',
            'rememberMeUid': '',
            'rememberMePwd': '',
            'sid': '',
            'token': '',
            'deviceType': 'pc',
            'ssoId': '',
            'phone': '',
            '_CACHE_LOGIN_TIME_': '1684293621436',
            'redirect_url': 'null',
            'lang': 'cn',
            'pwdEncode': 'RSA',
            'timeZone': '8'
        }
        
        try:
            print("正在登录EAP3系统...")
            response = self.session.post(url, data=post_data, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            response_data = data.get('data', {})
            self.sid = response_data.get('sid')
            self.token = response_data.get('token')
            
            if self.sid and self.token:
                sid_display = self.sid[:20] if self.sid else "unknown"
                print(f"✓ 登录成功!")
                return True
            else:
                print(f"✗ 登录失败: {data}")
                return False
                
        except Exception as e:
            print(f"✗ 登录异常: {e}")
            return False
    
    def search_product(self, product_name: str, max_pages: int = 100) -> List[Dict]:
        """
        查询产品信息
        
        Args:
            product_name: 要查询的产品名称/型号
            max_pages: 最大页数
            
        Returns:
            List[Dict]: 查询结果列表
        """
        if not self.sid:
            print("未登录，请先调用login()")
            return []
        
        url = f"{self.base_url}/r/jd"
        all_results = []
        page_nb = 1
        page_all = None
        
        condition_json = json.dumps({
            "cond": {
                "likeC": [{
                    "Type": "TEXT",
                    "Compare": "like",
                    "Field": "ITEM_DESCOBJ_47E882CCCE5D4E4880099621CE0E1684",
                    "FieldName": "物料描述",
                    "ConditionValue": product_name
                }]
            },
            "tcond": {"qk": ""}
        }, ensure_ascii=False)
        
        print(f"\n开始查询: '{product_name}'")
        start_time = time.time()
        
        while page_nb <= max_pages:
            post_data_dict = {
                'cmd': 'CLIENT_DW_DATA_GRIDJSON',
                'sid': self.sid,
                'appId': 'com.awspaas.user.apps.tengen.service',
                'pageNow': str(page_nb),
                'dwViewId': 'obj_3fc64424619d4af9b54d91ea141eda9e',
                'processGroupId': 'obj_399181a0bbdb426094d1fdc84ff13934',
                'processGroupName': 'NEW天正电气物料价格查询ES',
                'limit': '15',
                'condition': condition_json
            }
            
            try:
                response = self.session.post(url, data=post_data_dict, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                items = data.get('data', {}).get('maindata', {}).get('items', [])
                
                if page_nb == 1:
                    page_all = data.get('data', {}).get('maindata', {}).get('pageCount', 0)
                    total_count = data.get('data', {}).get('maindata', {}).get('totalCount', 0)
                    print(f"  共 {total_count} 条记录，{page_all} 页")
                    
                    if page_all == 0 or not items:
                        print(f"  未查询到 '{product_name}' 的相关数据")
                        return []
                
                for item in items:
                    result = {
                        '名称': item.get('MIDDLE', ''),
                        '物料编码': item.get('ITEM_NUM', ''),
                        '货期': item.get('PRODUCT_CYCLE', ''),
                        '型号': item.get('ITEM_DESC', ''),
                        '面价': item.get('PRICE', ''),
                        '单位': item.get('UNIT', ''),
                        '品牌': item.get('BRAND', ''),
                    }
                    all_results.append(result)
                
                if page_all is not None and page_nb >= page_all:
                    break
                    
                page_nb += 1
                time.sleep(0.3)
                
            except Exception as e:
                print(f"  查询异常 (页码{page_nb}): {e}")
                break
        
        elapsed = time.time() - start_time
        print(f"✓ 查询完成: 共 {len(all_results)} 条记录, 耗时 {elapsed:.2f} 秒")
        
        return all_results


def query_tgw1n_price(model_pattern: str) -> List[Dict]:
    """
    查询TGW1N系列断路器价格
    
    Args:
        model_pattern: 型号关键词，如 "TGW1N-2000/3P 2000A 抽屉"
        
    Returns:
        查询结果列表
    """
    client = TengenEAP3Client()
    
    if not client.login():
        print("登录失败")
        return []
    
    return client.search_product(model_pattern, max_pages=50)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "TGW1N-2000/3P 2000A 抽屉"
    
    results = query_tgw1n_price(query)
    
    if results:
        print(f"\n找到 {len(results)} 条记录:")
        for i, item in enumerate(results[:10], 1):
            print(f"\n{i}. 物料编码: {item['物料编码']}")
            print(f"   型号: {item['型号']}")
            print(f"   面价: {item['面价']}")
            print(f"   货期: {item['货期']}")
    else:
        print("未找到匹配记录")
