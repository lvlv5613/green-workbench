# Vercel Serverless: 抖音爆款 API
# 访问 /api/douyin?type=viral 或 /api/douyin?type=products
import json
import urllib.request

def fetch_json(url, timeout=10):
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except:
        return None

def get_viral():
    data = fetch_json('https://tenapi.cn/v2/douyinvideo')
    if data and 'data' in data:
        result = []
        for item in data['data'][:20]:
            if isinstance(item, dict):
                result.append({
                    'title': item.get('title', item.get('name', '')),
                    'author': item.get('author', item.get('nickname', '')),
                    'likes': item.get('likes', item.get('play', '')),
                    'plays': item.get('plays', ''),
                    'url': item.get('url', ''),
                    'tag': item.get('tag', '热门')
                })
        if result:
            return result
    return []

def get_products():
    data = fetch_json('https://tenapi.cn/v2/douyingoods')
    if data and 'data' in data:
        result = []
        for item in data['data'][:20]:
            if isinstance(item, dict):
                result.append({
                    'name': item.get('name', item.get('title', '')),
                    'price': item.get('price', ''),
                    'sales': item.get('sales', item.get('sold', '')),
                    'commission': item.get('commission', ''),
                    'url': item.get('url', ''),
                    'image': item.get('image', item.get('cover', ''))
                })
        if result:
            return result
    return []

def handler(req):
    from urllib.parse import parse_qs
    url = req.url if hasattr(req, 'url') else str(req)
    dtype = 'viral'
    if '?' in url:
        qs = parse_qs(url.split('?')[1])
        dtype = qs.get('type', ['viral'])[0]
    result = get_viral() if dtype == 'viral' else get_products()
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'list': result}, ensure_ascii=False)
    }
