const CACHE='zoo-zagreb-v2';
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(['/','/manifest.webmanifest','/favicon.svg'])).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('zoo-zagreb-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const request=event.request,url=new URL(request.url);if(request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
  if(request.mode==='navigate'){event.respondWith(fetch(request).then(response=>{if(response.ok&&response.type==='basic'){const copy=response.clone();event.waitUntil(caches.open(CACHE).then(cache=>cache.put('/',copy)));}return response;}).catch(()=>caches.match('/').then(r=>r||Response.error())));return;}
  if(url.pathname.endsWith('.glb')){event.respondWith(fetch(request,{cache:'no-cache'}).then(response=>{if(response.ok&&response.type==='basic'){const copy=response.clone();event.waitUntil(caches.open(CACHE).then(cache=>cache.put(request,copy)));}return response;}).catch(()=>caches.match(request).then(r=>r||Response.error())));return;}
  if(!/\.(js|css|glb|wasm|png|svg|webmanifest)$/.test(url.pathname))return;
  event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(response=>{if(response.ok&&response.type==='basic'){const copy=response.clone();event.waitUntil(caches.open(CACHE).then(cache=>cache.put(request,copy)));}return response;})));
});
