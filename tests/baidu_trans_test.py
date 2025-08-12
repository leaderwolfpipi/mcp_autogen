# -*- coding: utf-8 -*-

# This code shows an example of text translation from English to Simplified-Chinese.
# This code runs on Python 2.7.x and Python 3.x.
# You may install `requests` to run this code: pip install requests
# Please refer to `https://api.fanyi.baidu.com/doc/21` for complete api document

import requests
import random
import json

token = '24.1179e24d65f1a11243d36c17e340c41e.2592000.1756312814.282335-119632166'
url = 'https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1?access_token=' + token

q = 'hello fuck you.' # example: hello
# For list of language codes, please refer to `https://ai.baidu.com/ai-doc/MT/4kqryjku9#语种列表`
from_lang = 'en' # example: en
to_lang = 'zh' # example: zh
term_ids = '' # 术语库id，多个逗号隔开


# Build request
headers = {'Content-Type': 'application/json'}
payload = {'q': q, 'from': from_lang, 'to': to_lang, 'termIds' : term_ids}

# Send request
r = requests.post(url, params=payload, headers=headers)
result = r.json()

# Show response
print(json.dumps(result, indent=4, ensure_ascii=False))