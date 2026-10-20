// The service worker for the owner's phone alerts (Web Push). It does two things only: show a notification when the server pushes one, and open or focus the site when it is tapped.
// A notification with the same tag (the same TRADE) replaces the earlier one and still alerts (renotify), so a sell or a settlement takes the place of that trade's buy alert. It caches nothing, intercepts no request and makes no network call of its own. The text it shows comes from the push message the owner's own Cloud Function sent.
self.addEventListener('install', function(){ self.skipWaiting(); });
self.addEventListener('activate', function(event){ event.waitUntil(self.clients.claim()); });
self.addEventListener('push', function(event){
  var d = {};
  try { d = event.data ? event.data.json() : {}; } catch(e){ d = { body: event.data ? event.data.text() : '' }; }
  event.waitUntil(self.registration.showNotification(String(d.title || 'Shwoopnet').slice(0, 80), {
    body: String(d.body || '').slice(0, 160), tag: String(d.tag || 'shwoopnet'), renotify: true, icon: 'apple-touch-icon.png', badge: 'apple-touch-icon.png'
  }));
});
self.addEventListener('notificationclick', function(event){
  event.notification.close();
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(list){
    for(var i = 0; i < list.length; i++){ if('focus' in list[i]){ return list[i].focus(); } }
    return self.clients.openWindow('./');
  }));
});
