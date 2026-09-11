(() => {
 const input=document.querySelector('#lp-library-search,[data-library-search]');
 if(!input)return;
 const items=[...document.querySelectorAll('[data-library-item]')],result=document.getElementById('lp-library-results'),clear=document.querySelector('[data-library-clear]'),empty=document.querySelector('#lp-library-empty,#noresults'),quick=document.querySelector('[data-library-quick]');
 const city=input.id==='lp-library-search',noun=city?'city':'community',plural=city?'cities':'communities';
 const normalize=value=>value.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim().replace(/\s+/g,' ');
 const update=()=>{
  const q=normalize(input.value);let count=0;
  items.forEach(item=>{const match=!q||normalize(item.dataset.libraryName).includes(q);item.hidden=!match;item.style.display=match?'':'none';if(match)count++;});
  result.textContent=q?count+' '+(count===1?noun:plural)+' found for “'+input.value.trim()+'”':items.length+' '+(items.length===1?noun:plural)+' · A–Z';
  clear.hidden=!input.value;if(quick)quick.hidden=!!q;
  if(empty){empty.hidden=count>0;empty.classList.toggle('hidden',count>0);}
 };
 input.addEventListener('input',update);input.addEventListener('search',update);
 clear.addEventListener('click',()=>{input.value='';update();input.focus();});update();
})();
