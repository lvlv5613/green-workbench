# Vercel Serverless: 热搜 API
# 访问 /api/hot?platform=weibo
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

def fetch_json(url, headers=None, timeout=10):
    try:
        req = urllib.request.Request(url)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except:
        return None

def get_weibo():
    data = fetch_json('https://weibo.com/ajax/side/hotSearch', {'Referer': 'https://weibo.com', 'Accept': 'application/json'})
    if data and 'data' in data and 'realtime' in data['data']:
        return [{'text': i.get('note', i.get('word', '')), 'hot': str(i.get('num', '')), 'url': f"https://s.weibo.com/weibo?q=%23{i.get('word', '')}%23"} for i in data['data']['realtime'][:25]]
    data = fetch_json('https://api.vvhan.com/api/hotlist/wbHot')
    if data and 'data' in data:
        return [{'text': i.get('name', ''), 'hot': str(i.get('hot', '')), 'url': i.get('url', '')} for i in data['data'][:25] if isinstance(i, dict)]
    return []

def get_douyin():
    data = fetch_json('https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/')
    if data and 'word_list' in data:
        return [{'text': i.get('word', ''), 'hot': str(i.get('hot_value', '')), 'url': ''} for i in data['word_list'][:25]]
    data = fetch_json('https://api.vvhan.com/api/hotlist/dy')
    if data and 'data' in data and isinstance(data['data'], list):
        return [{'text': i.get('name', ''), 'hot': str(i.get('hot', '')), 'url': ''} for i in data['data'][:25] if isinstance(i, dict)]
    return []

def get_bilibili():
    data = fetch_json('https://app.bilibili.com/x/v2/show/popular/index')
    if data and 'data' in data:
        items = data['data']
        if isinstance(items, list):
            return [{'text': i.get('title', ''), 'hot': f"播放{i.get('stat',{}).get('view',0)//10000}万", 'url': f"https://www.bilibili.com/video/{i.get('bvid','')}"} for i in items[:25]]
    return []

def get_zhihu():
    data = fetch_json('https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=25', {'referer': 'https://www.zhihu.com/hot'})
    if data and 'data' in data:
        return [{'text': i.get('target',{}).get('title',''), 'hot': str(i.get('detail_text','')), 'url': i.get('target',{}).get('url','')} for i in data['data'][:25]]
    data = fetch_json('https://api.vvhan.com/api/hotlist/zhihu')
    if data and 'data' in data and isinstance(data['data'], list):
        return [{'text': i.get('name', ''), 'hot': str(i.get('hot', '')), 'url': i.get('url', '')} for i in data['data'][:25] if isinstance(i, dict)]
    return []

def get_toutiao():
    data = fetch_json('https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc')
    if data and 'data' in data:
        return [{'text': i.get('Title', ''), 'hot': str(i.get('HotValue', '')), 'url': i.get('Url', '')} for i in data['data'][:25]]
    return []

FETCHERS = {'weibo': get_weibo, 'douyin': get_douyin, 'bilibili': get_bilibili, 'zhihu': get_zhihu, 'toutiao': get_toutiao}

def handler(req):
    from urllib.parse import parse_qs
    url = req.url if hasattr(req, 'url') else str(req)
    platform = 'weibo'
    if '?' in url:
        qs = parse_qs(url.split('?')[1])
        platform = qs.get('platform', ['weibo'])[0]
    fetcher = FETCHERS.get(platform, get_weibo)
    result = fetcher()
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'list': result}, ensure_ascii=False)
    }
