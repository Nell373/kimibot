/**
 * LINE 智能記帳與提醒助手 - Service Worker
 */

// 緩存名稱與版本
const CACHE_NAME = 'linebot-finance-v1';

// 需要緩存的資源
const CACHE_URLS = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/templates/index.html',
    '/static/assets/icon-72x72.png',
    '/static/assets/icon-96x96.png',
    '/static/assets/icon-128x128.png',
    '/static/assets/icon-144x144.png',
    '/static/assets/icon-152x152.png',
    '/static/assets/icon-192x192.png',
    '/static/assets/icon-384x384.png',
    '/static/assets/icon-512x512.png'
];

// 安裝事件 - 緩存核心資源
self.addEventListener('install', (event) => {
    console.log('Service Worker: 安裝中...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: 開啟緩存...');
                return cache.addAll(CACHE_URLS);
            })
            .then(() => self.skipWaiting())
    );
});

// 啟動事件 - 清理舊版本緩存
self.addEventListener('activate', (event) => {
    console.log('Service Worker: 啟動中...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: 清理舊緩存 ', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// 請求攔截事件 - 實現離線功能
self.addEventListener('fetch', (event) => {
    console.log('Service Worker: 攔截請求 ', event.request.url);
    
    // 僅攔截GET請求
    if (event.request.method !== 'GET') return;
    
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // 如果在緩存中找到相符的資源，則返回緩存的資源
                if (response) {
                    console.log('Service Worker: 使用緩存資源 ', event.request.url);
                    return response;
                }
                
                // 如果緩存中沒有，則從網絡獲取
                console.log('Service Worker: 從網絡獲取資源 ', event.request.url);
                return fetch(event.request)
                    .then((newResponse) => {
                        // 不緩存API請求
                        if (event.request.url.includes('/api/')) {
                            return newResponse;
                        }
                        
                        // 複製響應以便緩存
                        let responseToCache = newResponse.clone();
                        
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });
                            
                        return newResponse;
                    });
            })
            .catch(() => {
                // 離線時無法獲取新資源，顯示離線頁面
                if (event.request.url.includes('/static/templates/')) {
                    return caches.match('/static/templates/offline.html');
                }
            })
    );
}); 