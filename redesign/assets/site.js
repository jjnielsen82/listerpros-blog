(() => {
 'use strict';
 const button=document.getElementById('lp-menu-button'),menu=document.getElementById('lp-mobile-menu');
 const close=()=>{if(!button||!menu)return;menu.hidden=true;button.setAttribute('aria-expanded','false');button.setAttribute('aria-label','Open navigation')};
 button?.addEventListener('click',()=>{const open=button.getAttribute('aria-expanded')!=='true';menu.hidden=!open;button.setAttribute('aria-expanded',String(open));button.setAttribute('aria-label',open?'Close navigation':'Open navigation')});
 menu?.querySelectorAll('a').forEach(a=>a.addEventListener('click',close));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&button?.getAttribute('aria-expanded')==='true'){close();button.focus()}});
 window.matchMedia?.('(min-width: 1101px)').addEventListener('change',e=>{if(e.matches)close()});
 const clean=p=>p.replace(/\/index\.html$/,'/').replace(/\.html$/,'').replace(/\/$/,'')||'/';
 document.querySelectorAll('.lp-header a[href]').forEach(a=>{const u=new URL(a.href,location.href);if(u.origin===location.origin&&clean(u.pathname)===clean(location.pathname))a.setAttribute('aria-current','page')});
 // Homepage package controls retain published size tiers; booking stays a normal link.
 const prices=[[139,169,199],[199,249,299],[419,519,569],[769,869,969]], labels=['Up to 2,000 sq ft','2,001–4,000 sq ft','4,001+ sq ft'],counts=['20–35','40–45','50–55'];
 document.querySelectorAll('.lp-home [data-size]').forEach(b=>b.addEventListener('click',()=>{const size=Number(b.dataset.size);document.querySelectorAll('.lp-home [data-size]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('.lp-home [data-price]').forEach(x=>x.textContent='$'+prices[+x.dataset.price][size]);document.querySelectorAll('.lp-home .sqft').forEach(x=>x.textContent=labels[size]);document.querySelectorAll('.lp-home .photo-count').forEach(x=>x.textContent=counts[size])}));
 document.querySelectorAll('.size-btn').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.size==='small'));b.addEventListener('click',()=>document.querySelectorAll('.size-btn').forEach(x=>x.setAttribute('aria-pressed',String(x===b))))});
 // Track the handoff without blocking it or changing the order-form URL.
 document.addEventListener('click',e=>{const a=e.target.closest?.('a[href]');if(!a)return;try{const u=new URL(a.href,location.href);if(u.hostname==='media.listerpros.com'&&u.pathname.startsWith('/order-forms/'))window.gtag?.('event','booking_click',{link_url:u.href.split('?')[0],page_path:location.pathname,placement:a.closest('.lp-header')?'header':a.closest('.lp-footer')?'footer':'content',transport_type:'beacon'})}catch{}});
})();
