// 绿绿工作台 Service Worker
// 缓存策略：核心资源优先缓存，API 请求网络优先

const CACHE_NAME = 'green-workbench-v5';
const CORE_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
    '/icon-192.png',
    '/icon-512.png',
    '/apple-touch-icon.png',
    '/favicon.png'
];

// 安装：预缓存核心资源
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(CORE_ASSETS).catch(() => {}))
            .then(() => self.skipWaiting())
    );
});

// 激活：清理旧缓存
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.map(k => k !== CACHE_NAME ? caches.delete(k) : null))
        ).then(() => self.clients.claim())
    );
});

// 请求拦截
self.addEventListener('fetch', (event) => {
    const req = event.request;

    // 跳过非 GET 请求
    if (req.method !== 'GET') return;

    // API 请求：网络优先，失败时不缓存（热搜/抖音等实时数据）
    if (req.url.includes('/api/')) {
        event.respondWith(
            fetch(req).catch(() => {
                return new Response(JSON.stringify({ list: [] }), {
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
        return;
    }

    // 静态资源：缓存优先，网络兜底
    event.respondWith(
        caches.match(req).then(cached => {
            if (cached) return cached;
            return fetch(req).then(resp => {
                // 成功获取则缓存
                if (resp.ok) {
                    const clone = resp.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(req, clone));
                }
                return resp;
            }).catch(() => {
                // 离线且无缓存，返回首页（SPA 兜底）
                if (req.mode === 'navigate') {
                    return caches.match('/index.html');
                }
            });
        })
    );
});

// 接收更新消息
self.addEventListener('message', (event) => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
});
