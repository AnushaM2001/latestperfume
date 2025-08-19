// static/sw.js
self.addEventListener("push", function(e) {
  const data = e.data.json();
  const title = data.title;
  const body = data.body;

  self.registration.showNotification(title, {
    body: body,
    icon: '/static/images2/hi1.png'
  });
});
