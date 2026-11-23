const e=new BroadcastChannel(`myfaveTTT:params-guard`);chrome.runtime.onMessage.addListener(function(t,n,r){if(n.id!==chrome.runtime.id||!t||typeof t!=`object`)return;let i=t;i.type===`myfaveTTT:params-guard:capture`&&typeof i.id==`string`&&typeof i.url==`string`&&(e.postMessage({type:i.type,id:i.id,url:i.url}),r())});function t(){return location.hostname!==`www.tiktok.com`||self!==top?!1:!![`/`,`/explore`,`/foryou`].includes(location.pathname)}t()&&(r(),n());function n(){let e=document.createElement(`aside`);e.id=`myfaveTTT-container`;let t=document.createElement(`iframe`);t.src=chrome.runtime.getURL(`rl.html`),t.name=`sidebarTTT`,t.id=`myfaveTTT`,e.appendChild(t),document.body.classList.add(`pushed-by-myfaveTTT`),document.body.prepend(e)}function r(){let e=document.createElement(`script`);e.src=chrome.runtime.getURL(`s.js`),e.type=`module`,document.head.appendChild(e)}
// Cookie relay between webpage and background service worker
window.addEventListener('message', function(evt){
  if(evt && evt.data && evt.data.type === 'myfaveTTT:get_cookies'){
    chrome.runtime.sendMessage({type: 'GET_TIKTOK_COOKIES'}, function(res){
      window.postMessage({type: 'myfaveTTT:cookies_result', result: res}, '*');
    });
  }
});
