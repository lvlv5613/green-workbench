#!/usr/bin/env python3
"""
绿绿工作台后端服务器
提供实时热搜数据和抖音爆款数据 API
"""

import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading
import time
import os
import re

# ========== 热搜数据抓取 ==========

def fetch_json(url, headers=None, timeout=10):
    """通用 JSON 抓取"""
    try:
        req = urllib.request.Request(url)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        print(f"[ERROR] fetch {url}: {e}")
        return None

def get_weibo_hot():
    """微博热搜"""
    # 方式1：官方API
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://weibo.com',
        'Accept': 'application/json'
    }
    data = fetch_json('https://weibo.com/ajax/side/hotSearch', headers)
    if data and 'data' in data and 'realtime' in data['data']:
        result = []
        for item in data['data']['realtime'][:25]:
            result.append({
                'text': item.get('note', item.get('word', '')),
                'hot': str(item.get('num', '')),
                'url': f"https://s.weibo.com/weibo?q=%23{item.get('word', '')}%23"
            })
        if result:
            return result
    # 方式2：备用API
    for backup_url in ['https://tenapi.cn/v2/weibohot', 'https://api.vvhan.com/api/hotlist/wbHot']:
        data = fetch_json(backup_url)
        if data:
            result = []
            # tenapi格式
            if 'data' in data and isinstance(data['data'], list):
                for item in data['data'][:25]:
                    if isinstance(item, dict):
                        result.append({
                            'text': item.get('name', item.get('title', '')),
                            'hot': str(item.get('hot', item.get('hotValue', ''))),
                            'url': item.get('url', '')
                        })
            # vvhan格式
            elif 'data' in data and isinstance(data['data'], list):
                for item in data['data'][:25]:
                    if isinstance(item, dict):
                        result.append({
                            'text': item.get('name', item.get('title', '')),
                            'hot': str(item.get('hot', '')),
                            'url': item.get('url', '')
                        })
            if result:
                return result
    return []

def get_douyin_hot():
    """抖音热榜"""
    # 方式1：官方API
    data = fetch_json('https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/')
    if data and 'word_list' in data:
        result = []
        for item in data['word_list'][:25]:
            result.append({
                'text': item.get('word', ''),
                'hot': str(item.get('hot_value', '')),
                'url': ''
            })
        if result:
            return result
    # 方式2：备用API
    for backup_url in ['https://tenapi.cn/v2/douyinhot', 'https://api.vvhan.com/api/hotlist/dy']:
        data = fetch_json(backup_url)
        if data and 'data' in data:
            result = []
            items = data['data']
            if isinstance(items, list):
                for item in items[:25]:
                    if isinstance(item, dict):
                        result.append({
                            'text': item.get('name', item.get('title', '')),
                            'hot': str(item.get('hot', '')),
                            'url': ''
                        })
            if result:
                return result
    return []

def get_bilibili_hot():
    """B站热门"""
    data = fetch_json('https://app.bilibili.com/x/v2/show/popular/index')
    if data and 'data' in data:
        items = data['data']
        if isinstance(items, list):
            result = []
            for item in items[:25]:
                stat = item.get('stat', {})
                result.append({
                    'text': item.get('title', ''),
                    'hot': f"播放{stat.get('view', 0)//10000}万",
                    'url': f"https://www.bilibili.com/video/{item.get('bvid', '')}"
                })
            return result
        elif isinstance(items, dict) and 'list' in items:
            result = []
            for item in items['list'][:25]:
                stat = item.get('stat', {})
                result.append({
                    'text': item.get('title', ''),
                    'hot': f"播放{stat.get('view', 0)//10000}万",
                    'url': f"https://www.bilibili.com/video/{item.get('bvid', '')}"
                })
            return result
    # 备用
    data = fetch_json('https://tenapi.cn/v2/bilihot')
    if data and 'data' in data:
        result = []
        for item in data['data'][:25]:
            if isinstance(item, dict):
                result.append({
                    'text': item.get('name', ''),
                    'hot': item.get('hot', ''),
                    'url': ''
                })
        return result
    return []

def get_zhihu_hot():
    """知乎热榜"""
    # 方式1：官方API
    headers = {'referer': 'https://www.zhihu.com/hot'}
    data = fetch_json('https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=25', headers)
    if data and 'data' in data:
        result = []
        for item in data['data'][:25]:
            target = item.get('target', {})
            result.append({
                'text': target.get('title', ''),
                'hot': str(item.get('detail_text', '')),
                'url': target.get('url', '')
            })
        if result:
            return result
    # 方式2：备用API
    for backup_url in ['https://tenapi.cn/v2/zhihuhot', 'https://api.vvhan.com/api/hotlist/zhihu']:
        data = fetch_json(backup_url)
        if data and 'data' in data:
            result = []
            items = data['data']
            if isinstance(items, list):
                for item in items[:25]:
                    if isinstance(item, dict):
                        result.append({
                            'text': item.get('name', item.get('title', '')),
                            'hot': str(item.get('hot', '')),
                            'url': item.get('url', '')
                        })
            if result:
                return result
    return []

def get_toutiao_hot():
    """头条热榜"""
    data = fetch_json('https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc')
    if data and 'data' in data:
        result = []
        for item in data['data'][:25]:
            result.append({
                'text': item.get('Title', ''),
                'hot': str(item.get('HotValue', '')),
                'url': item.get('Url', '')
            })
        return result
    # 备用
    data = fetch_json('https://tenapi.cn/v2/toutiaohot')
    if data and 'data' in data:
        result = []
        for item in data['data'][:25]:
            if isinstance(item, dict):
                result.append({
                    'text': item.get('name', ''),
                    'hot': item.get('hot', ''),
                    'url': ''
                })
        return result
    return []

# 热搜缓存
hot_cache = {}
hot_cache_time = {}

def get_hot_search(platform):
    """获取热搜（带5分钟缓存）"""
    now = time.time()
    if platform in hot_cache and platform in hot_cache_time:
        if now - hot_cache_time[platform] < 300:  # 5分钟缓存
            return hot_cache[platform]

    fetchers = {
        'weibo': get_weibo_hot,
        'douyin': get_douyin_hot,
        'bilibili': get_bilibili_hot,
        'zhihu': get_zhihu_hot,
        'toutiao': get_toutiao_hot
    }
    fetcher = fetchers.get(platform)
    if not fetcher:
        return []
    result = fetcher()
    hot_cache[platform] = result
    hot_cache_time[platform] = now
    return result

# ========== 抖音爆款数据 ==========

# 抖音热门视频（模拟实时数据，实际中需要爬虫或API）
def get_douyin_viral():
    """获取抖音3天爆款视频"""
    # 尝试从 API 获取
    data = fetch_json('https://tenapi.cn/v2/douyinvideo')
    if data and 'data' in data:
        result = []
        for item in data.get('data', [])[:20]:
            if isinstance(item, dict):
                result.append({
                    'title': item.get('title', item.get('name', '')),
                    'author': item.get('author', item.get('nickname', '')),
                    'likes': item.get('likes', item.get('play', '')),
                    'plays': item.get('plays', ''),
                    'url': item.get('url', ''),
                    'cover': item.get('cover', ''),
                    'tag': item.get('tag', '热门')
                })
        if result:
            return result

    # 备用：返回空列表，前端会显示提示
    return []

def get_douyin_products():
    """获取抖音带货爆款选品"""
    # 尝试从 API 获取
    data = fetch_json('https://tenapi.cn/v2/douyingoods')
    if data and 'data' in data:
        result = []
        for item in data.get('data', [])[:20]:
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

# ========== HTTP 服务器 ==========

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        # API 路由
        if self.path.startswith('/api/hot/'):
            platform = self.path.replace('/api/hot/', '').split('?')[0]
            self.handle_hot_api(platform)
            return
        elif self.path.startswith('/api/douyin/viral'):
            self.handle_douyin_viral()
            return
        elif self.path.startswith('/api/douyin/products'):
            self.handle_douyin_products()
            return
        else:
            # 静态文件
            super().do_GET()

    def guess_type(self, path):
        """确保正确的 MIME type"""
        if path.endswith('.json'):
            return 'application/json; charset=utf-8'
        if path.endswith('.js'):
            return 'application/javascript; charset=utf-8'
        if path.endswith('.png'):
            return 'image/png'
        if path.endswith('.webmanifest'):
            return 'application/manifest+json'
        return super().guess_type(path)

    def handle_hot_api(self, platform):
        result = get_hot_search(platform)
        self.send_json({'list': result})

    def handle_douyin_viral(self):
        result = get_douyin_viral()
        self.send_json({'list': result})

    def handle_douyin_products(self):
        result = get_douyin_products()
        self.send_json({'list': result})

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        # 简化日志
        if '/api/' in (args[0] if args else ''):
            super().log_message(format, *args)

def main():
    port = 8080
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = partial(CustomHandler, directory=os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(('0.0.0.0', port), handler)
    print(f"🌿 绿绿工作台服务器启动中...")
    print(f"   地址: http://localhost:{port}")
    print(f"   热搜API: /api/hot/<weibo|douyin|bilibili|zhihu|toutiao>")
    print(f"   抖音爆款: /api/douyin/viral")
    print(f"   抖音选品: /api/douyin/products")
    print(f"   按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()

if __name__ == '__main__':
    main()
