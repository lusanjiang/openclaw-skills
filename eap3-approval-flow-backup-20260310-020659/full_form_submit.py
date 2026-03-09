#!/usr/bin/env python3
"""
EAP3 纯 Python 审批 - 完整表单提交流程
尝试模拟浏览器完整提交过程
"""

import requests
import re
import json
from datetime import datetime

EAP3_URL = 'https://eap3.tengen.com.cn'
USER_ID = 'lusanjiang'
ENCRYPTED_PWD = '345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39'

def main():
    session = requests.Session()
    
    # 步骤1: 登录
    print('步骤1: 登录...')
    resp = session.post(f'{EAP3_URL}/r/w', data={
        'userid': USER_ID, 'pwd': ENCRYPTED_PWD, 'cmd': 'com.actionsoft.apps.tengen.login',
        'deviceType': 'pc', 'lang': 'cn', 'pwdEncode': 'RSA', 'timeZone': '8',
        '_CACHE_LOGIN_TIME_': str(int(datetime.now().timestamp() * 1000))
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
    sid = resp.json()['data']['sid']
    print(f'✓ 登录成功，SID: {sid[:20]}...')
    
    # 步骤2: 获取待办
    print('\\n步骤2: 获取待办...')
    resp2 = session.post(f'{EAP3_URL}/r/jd', params={'sid': sid, 'cmd': 'com.actionsoft.apps.notification_load_unread_msg'}, timeout=30)
    data2 = resp2.json()
    
    # 找到第一个 XZ38 待办
    target_item = None
    for item in data2.get('data', {}).get('list', []):
        content = item.get('content', '')
        if 'XZ38' in content and '定制' in content:
            target_item = item
            break
    
    if not target_item:
        print('✗ 没有找到 XZ38 待办')
        return
    
    task_inst_id = target_item.get('sourceId', '')
    process_inst_id = target_item.get('notifyContent', {}).get('processInstId', '')
    user_name = target_item.get('userName', '')
    
    print(f'✓ 找到待办: {user_name}')
    print(f'  taskInstId: {task_inst_id}')
    print(f'  processInstId: {process_inst_id}')
    
    # 步骤3: 获取表单页面（模拟浏览器加载）
    print('\\n步骤3: 获取表单页面...')
    form_params = {
        'sid': sid,
        'cmd': 'CLIENT_BPM_FORM_MAIN_PAGE_OPEN',
        'processInstId': process_inst_id,
        'taskInstId': task_inst_id,
        'openState': '1'
    }
    resp3 = session.get(f'{EAP3_URL}/r/w', params=form_params, timeout=30)
    html = resp3.text
    print(f'✓ 表单页面加载成功，长度: {len(html)}')
    
    # 步骤4: 提取表单关键字段
    print('\\n步骤4: 提取表单字段...')
    
    # 提取隐藏字段
    hidden_fields = {}
    for match in re.finditer(r'<input[^\u003e]*type=["\']hidden["\'][^\u003e]*name=["\']([^"\']+)["\'][^\u003e]*value=["\']([^"\']*)["\']', html):
        name, value = match.groups()
        hidden_fields[name] = value
    
    print(f'  找到 {len(hidden_fields)} 个隐藏字段')
    for k, v in list(hidden_fields.items())[:5]:
        print(f'    {k}: {v[:50] if len(v) > 50 else v}')
    
    # 步骤5: 构造完整的表单提交数据
    print('\\n步骤5: 构造提交数据...')
    
    # 基础表单数据
    submit_data = {
        'sid': sid,
        'cmd': 'CLIENT_BPM_FORM_SUBMIT',
        'processInstId': process_inst_id,
        'taskInstId': task_inst_id,
        'buttonId': 'BTN_TRANSACT',
        # 审批结果
        'NEED_RESULT': '已核实请后台支持',
        'DISTRIBUTE_TYPE': '已核实请后台支持'
    }
    
    # 添加隐藏字段（但排除可能冲突的字段）
    for k, v in hidden_fields.items():
        if k not in submit_data and not k.startswith('cmd'):
            submit_data[k] = v
    
    print(f'  提交数据包含 {len(submit_data)} 个字段')
    
    # 步骤6: 尝试提交（使用 /r/jd 接口）
    print('\\n步骤6: 尝试提交审批...')
    resp_submit = session.post(f'{EAP3_URL}/r/jd', data=submit_data, timeout=30)
    
    print(f'  状态码: {resp_submit.status_code}')
    print(f'  Content-Type: {resp_submit.headers.get("Content-Type", "")}')
    
    if 'json' in resp_submit.headers.get('Content-Type', ''):
        try:
            result = resp_submit.json()
            print(f'\\n响应: {json.dumps(result, ensure_ascii=False, indent=2)}')
            
            if result.get('result') == 'ok':
                print('\\n✅ 审批成功!')
            else:
                print(f'\\n❌ 审批失败: {result.get("msg", "未知错误")}')
        except Exception as e:
            print(f'\\n⚠️ 无法解析 JSON: {e}')
            print(f'响应: {resp_submit.text[:500]}')
    else:
        print(f'\\n⚠️ 返回 HTML:')
        print(resp_submit.text[:500])

if __name__ == '__main__':
    main()
