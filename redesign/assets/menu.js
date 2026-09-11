(() => {
 'use strict';
 const goal=document.getElementById('mp-goal');
 const goalMatches={
  '0':{packages:['0','1','2','3'],message:'All four packages meet this goal: each includes professional photography. Compare the extras below.'},
  '1':{packages:['1','3'],message:'Essential and Elite meet this goal. Essential includes a Zillow 3D tour and floor plan; Elite includes Matterport and a floor plan.'},
  '2':{packages:['2','3'],message:'Premier and Elite meet this goal: both include walkthrough video and an agent on-camera intro.'},
  '3':{packages:['3'],message:'Elite meets this goal with professional photos, drone, video and a Matterport tour with floor plan.'}
 };
 const updateGoal=()=>{
  const match=goalMatches[goal.value];
  document.querySelectorAll('.mp-package').forEach(card=>card.dataset.recommended=String(!!match?.packages.includes(card.dataset.package)));
  document.getElementById('mp-choice-result').textContent=match?.message||'All four packages include professional photography.';
 };
 if(goal){goal.addEventListener('change',updateGoal);updateGoal();}
 const resourceButtons=[...document.querySelectorAll('[data-resource-filter]')],resources=[...document.querySelectorAll('[data-resource-category]')];
 resourceButtons.forEach(b=>b.addEventListener('click',()=>{resourceButtons.forEach(x=>x.setAttribute('aria-pressed',String(x===b)));resources.forEach(c=>c.hidden=b.dataset.resourceFilter!=='all'&&b.dataset.resourceFilter!==c.dataset.resourceCategory);const n=resources.filter(c=>!c.hidden).length;document.getElementById('mp-resource-status').textContent=n+' '+(n===1?'guide':'guides')+' to explore';}));
 document.querySelector('[data-team-presentation]')?.addEventListener('click',()=>{const select=document.getElementById('team-presentation');if(select){select.value='Yes, contact me to arrange a team presentation';}});
 const dialog=document.getElementById('lightbox');
 if(!dialog)return;
 const items=[...document.querySelectorAll('.portfolio-item')],filters=[...document.querySelectorAll('.filter-btn')];let index=0,active=[],opener=null,priorOverflow='';
 const filter=value=>{filters.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===value)));items.forEach(i=>{i.hidden=value!=='all'&&i.dataset.category!==value;i.classList.toggle('hidden',i.hidden)});document.getElementById('mp-gallery-count').textContent=items.filter(i=>!i.hidden).length+' photographs';};
 filters.forEach(b=>b.addEventListener('click',()=>filter(b.dataset.filter)));
 document.querySelectorAll('[data-gallery-jump]').forEach(a=>a.addEventListener('click',()=>filter(a.dataset.galleryJump)));
 const display=()=>{const item=active[index],original=item.querySelector('img'),image=dialog.querySelector('#lightbox-img');image.src=item.href;image.alt=original.alt;dialog.querySelector('#lightbox-caption').textContent=item.dataset.caption||original.alt;dialog.querySelector('#lightbox-counter').textContent=(index+1)+' / '+active.length;};
 items.forEach(item=>item.addEventListener('click',e=>{if(typeof dialog.showModal!=='function')return;e.preventDefault();opener=item;active=items.filter(x=>!x.hidden);index=active.indexOf(item);if(index<0)return;priorOverflow=document.body.style.overflow;display();dialog.showModal();document.body.style.overflow='hidden';dialog.querySelector('#lightbox-close').focus();}));
 const close=()=>dialog.close();
 dialog.addEventListener('close',()=>{document.body.style.overflow=priorOverflow;opener?.focus();});
 dialog.querySelector('#lightbox-close').addEventListener('click',close);
 dialog.querySelector('#lightbox-prev').addEventListener('click',()=>{index=(index-1+active.length)%active.length;display()});
 dialog.querySelector('#lightbox-next').addEventListener('click',()=>{index=(index+1)%active.length;display()});
 dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)close();}});
 dialog.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'){e.preventDefault();dialog.querySelector('#lightbox-prev').click()}if(e.key==='ArrowRight'){e.preventDefault();dialog.querySelector('#lightbox-next').click()}});
})();
