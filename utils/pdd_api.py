import time
from django.conf import settings
import hashlib
import requests
from django.core.cache import cache


class PddRequest:
    def __init__(self, req_type):
        self.params = {}
        self.host = "https://gw-api.pinduoduo.com/api/router"
        self.headers = {'Content-Type': 'application/json'}
        self.params['type'] = req_type
        self.params['client_id'] = settings.PDD_CLIENT_ID
        self.params['timestamp'] = str(int(time.time()))
        self.params['data_type'] = 'JSON'


class JpkRequest:
    def __init__(self):
        self.params = {}
        self.params['appid'] = settings.JPK_APP_ID
        self.params['appkey'] = settings.JPK_APP_SECRET
        self.params['sid'] = settings.JPK_SID
        self.params['pid'] = '42893128_305187033'
        self.params['custom_parameters'] = '19491001'


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


def search_keywords(r_params):
    try:
        cache.incr('search_keywords_count')
    except:
        cache.set('search_keywords_count', 1, timeout=None)
    request = PddRequest('pdd.ddk.goods.search')
    request.params['use_customized'] = 'false'
    request.params['with_coupon'] = 'false'
    user = pdd_auth_user()
    request.params['pid'] = user['pid']
    request.params['custom_parameters'] = user['custom_parameters']
    request.params['sort_type'] = 0
    request.params['page_size'] = 50
    if r_params.get('keyword'):
        request.params['keyword'] = r_params.get('keyword')
    if r_params.get('page'):
        request.params['page'] = int(r_params.get('page'))
    if r_params.get('list_id'):
        request.params['list_id'] = r_params.get('list_id')
    if r_params.get('cat_id'):
        request.params['cat_id'] = r_params.get('cat_id')
    if r_params.get('page_size'):
        request.params['page_size'] = r_params.get('page_size')
    request.params['sign'] = sign_params(request.params)
    resp = requests.post(request.host, json=request.params, headers=request.headers).json()
    success = resp.get('goods_search_response')
    if success:
        return success
    else:
        resp['req_params'] = request.params
        return resp


def goods_detail(goods_sign):
    try:
        cache.incr('goods_detail_count')
    except:
        cache.set('goods_detail_count', 1, timeout=None)
    request = PddRequest('pdd.ddk.goods.detail')
    request.params['need_sku_info'] = 'true'
    request.params['goods_sign'] = goods_sign
    user = pdd_auth_user()
    request.params['pid'] = user['pid']
    request.params['custom_parameters'] = user['custom_parameters']
    request.params['sign'] = sign_params(request.params)
    resp = requests.post(request.host, json=request.params, headers=request.headers).json()
    success = resp.get('goods_detail_response')
    if success:
        return success
    else:
        return resp


def child_cats(cat_id):
    request = PddRequest('pdd.goods.cats.get')
    request.params['parent_cat_id'] = cat_id
    request.params['sign'] = sign_params(request.params)
    resp = requests.post(request.host, json=request.params, headers=request.headers).json()
    success = resp.get('goods_cats_get_response', None).get('goods_cats_list', None)
    if success:
        return success
    else:
        return []


def cats_list(cat_id=0, cat_list=None):
    if cat_list is None:
        cat_list = []
    for child in child_cats(cat_id):
        cat_list.append(child)
        if child.get('level') <= 4:
            print(
                f'current list total: {len(cat_list)}, current list level: {child.get("level")}, current cat id: {child.get("cat_id")}')
            cats_list(child.get('cat_id'), cat_list)
    return cat_list


def jpk_goods_search(keywords, page=1, list_id=''):
    search_url = "http://api.jingpinku.com/pdd_get_goods_search/api"
    request = JpkRequest()
    request.params['use_customized'] = 'false'
    request.params['with_coupon'] = 'false'
    request.params['keyword'] = keywords
    request.params['sort_type'] = 0
    if page > 1:
        request.params['page'] = page
    if list_id != '':
        request.params['list_id'] = list_id
    resp = requests.get(search_url, params=request.params)
    if resp.json().get('code') == '0':
        return resp.json().get('data')
    else:
        return resp.json()


def pdd_auth_user():
    import random
    all_pid = [
        {"pid": "42893128_305187033", "custom_parameters": "19491001"},
        {"pid": "42893128_305099068", "custom_parameters": "9527"},
        {"pid": "42893128_305339946", "custom_parameters": "100001"},
        {"pid": "42893128_305341966", "custom_parameters": "100002"},
        {"pid": "42893128_305341966", "custom_parameters": "100003"},
        {"pid": "42893128_305341966", "custom_parameters": "100004"},
        {"pid": "42893128_305341966", "custom_parameters": "100006"},
        {"pid": "42893128_305341966", "custom_parameters": "100007"},
        {"pid": "42893128_305341966", "custom_parameters": "100008"},
        {"pid": "42893128_305341966", "custom_parameters": "100009"},
        {"pid": "42893128_305341966", "custom_parameters": "100010"},
        {"pid": "42893128_305341966", "custom_parameters": "100011"},
        {"pid": "42893128_305341966", "custom_parameters": "100012"},
        {"pid": "42893128_305341966", "custom_parameters": "100013"},
        {"pid": "42893128_305341966", "custom_parameters": "100014"},
        {"pid": "42893128_305341966", "custom_parameters": "100015"},
        {"pid": "42893128_305341966", "custom_parameters": "100016"},
        {"pid": "42893128_305341966", "custom_parameters": "100017"},
        {"pid": "42893128_305341966", "custom_parameters": "100018"},
        {"pid": "42893128_305341966", "custom_parameters": "100019"},
        {"pid": "42893128_305341966", "custom_parameters": "100020"},
    ]
    return random.choice(all_pid)
