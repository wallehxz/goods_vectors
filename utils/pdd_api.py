import time
from django.conf import settings
import hashlib
from urllib.parse import quote
from collections import OrderedDict
import requests
import json


class PddRequest:
    def __init__(self,  req_type):
        self.params = {}
        self.host = "https://gw-api.pinduoduo.com/api/router"
        self.headers = {'Content-Type': 'application/json'}
        self.params['type'] = req_type
        self.params['client_id'] = settings.PDD_CLIENT_ID
        self.params['timestamp'] = str(int(time.time()))
        self.params['data_type'] = 'JSON'
        self.params['page_size'] = 100
        self.params['pid'] = '42893128_305099068'
        self.params['custom_parameters'] = '9527'


def upper_md5(text):
    md5_hash = hashlib.md5()
    md5_hash.update(text.encode('utf-8'))  # 需要将字符串编码为字节
    return md5_hash.hexdigest().upper()


def sign_params(params):
    params_string = settings.PDD_CLIENT_SECRET
    params_array = []
    for key, val in params.items():
        params_array.append(f'{key}{val}')
    params_sorted = sorted(params_array)
    for item in params_sorted:
        params_string += item
    params_string += settings.PDD_CLIENT_SECRET
    print(params_string)
    return upper_md5(params_string)


def search_keywords(keywords, page=1, list_id=''):
    request = PddRequest('pdd.ddk.goods.search')
    request.params['keyword'] = keywords
    request.params['use_customized'] = 'false'
    request.params['with_coupon'] = 'false'
    request.params['sort_type'] = 0
    if page > 1:
        request.params['page'] = page
    if list_id != '':
        request.params['list_id'] = list_id
    request.params['sign'] = sign_params(request.params)
    resp = requests.post(request.host, json=request.params, headers=request.headers)
    return resp.json().get('goods_search_response')


def goods_detail(goods_sign):
    request = PddRequest('pdd.ddk.goods.detail')
    request.params['need_sku_info'] = 'true'
    request.params['goods_sign'] = goods_sign
    request.params['sign'] = sign_params(request.params)
    resp = requests.post(request.host, json=request.params, headers=request.headers)
    return resp.json()


