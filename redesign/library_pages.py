"""Searchable directories; preserve all original links and access-token logic."""
from bs4 import BeautifulSoup
from html import escape

def fragment(html):return BeautifulSoup(html,'html.parser')

def refine_library(s,path):
 if path=='community-photos/index.html':
  grid=s.select_one('main .grid');cards=grid.find_all('a',recursive=False);ranked=[]
  for a in cards:
   spans=a.find_all('span',recursive=False);name=spans[0].get_text(strip=True);count=int(spans[1].get_text(strip=True).replace(',',''));ranked.append((name,count,a['href']))
   a['data-library-name']=name;a['data-library-item']='';a['class']=['lp-city-card'];spans[1].string=f'{count} '+('community' if count==1 else 'communities')
  grid['id']='lp-library-list';grid['class']=['lp-city-grid']
  for a in sorted(cards,key=lambda x:x['data-library-name'].casefold()):grid.append(a.extract())
  quick=''.join(f'<a href="{escape(url)}">{escape(name)}</a>' for name,count,url in sorted(ranked,key=lambda x:-x[1])[:10])
  grid.insert_before(fragment(f'<section class="lp-library-quick" data-library-quick aria-labelledby="lp-quick-title"><h2 id="lp-quick-title">Quick links</h2><p>The 10 cities with the largest community collections.</p><div>{quick}</div></section>'))
  grid.insert_before(fragment(f'<div class="lp-library-tools"><label for="lp-library-search">Find your city</label><div class="lp-library-search-row"><input id="lp-library-search" class="lp-library-search" type="search" placeholder="Start typing a city, e.g. Scottsdale" autocomplete="off" aria-controls="lp-library-list" aria-describedby="lp-library-results"><button type="button" data-library-clear hidden>Clear search</button></div><h2>All cities · A–Z</h2><p id="lp-library-results" role="status" aria-live="polite">{len(cards)} cities</p></div>'))
  request=next((a for a in s.select('main a[href]') if 'Request a community' in a.get_text()),None)
  url=request['href'] if request else '/free-community-photos'
  grid.insert_after(fragment(f'<div class="lp-library-empty" id="lp-library-empty" hidden><h2>No matching city yet.</h2><p>Try another spelling, clear your search, or <a href="{escape(url)}">request your community</a>.</p></div>'))
  s.select_one('main h1').parent.append(fragment('<p class="lp-library-help">Choose a city, find your community, then view photos and request download access.</p>'))
 elif s.select_one('main #list') and s.select_one('main #filter'):
  grid=s.select_one('#list');grid['data-library-list']='';cards=grid.find_all('li',recursive=False)
  for li in cards:
   spans=li.a.find_all('span',recursive=False);li['data-library-name']=spans[0].get_text(strip=True);li['data-library-item']=''
   if len(spans)>1:
    count=spans[1].get_text(strip=True);spans[1].string=count+' '+('photo' if count=='1' else 'photos')
  for li in sorted(cards,key=lambda x:x['data-library-name'].casefold()):grid.append(li.extract())
  inp=s.select_one('#filter');inp['aria-controls']='list';inp['aria-describedby']='lp-library-results';inp['data-library-search']=''
  label=s.select_one('label[for="filter"]');label['class']=['lp-library-label'];label.string='Find your community'
  parent=inp.parent;parent['class']=['lp-library-tools'];inp.wrap(s.new_tag('div',attrs={'class':['lp-library-search-row']}))
  inp.insert_after(fragment('<button type="button" data-library-clear hidden>Clear search</button>'))
  parent.append(fragment(f'<p id="lp-library-results" role="status" aria-live="polite">{len(cards)} communities · A–Z</p>'))
  others=next((h for h in s.select('main h2') if h.get_text(strip=True)=='Other cities'),None)
  if others:
   links=others.find_next_sibling('div')
   if links:
    for a in sorted(links.find_all('a',recursive=False),key=lambda a:(a.get_text(strip=True)=='All cities',a.get_text(strip=True).casefold())):links.append(a.extract())
 return s
