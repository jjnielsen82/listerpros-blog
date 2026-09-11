from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
from html import escape
import json,re

def build(blog_source,output,theme):
 posts=[];tags=defaultdict(list);labels={}
 for p in blog_source.glob('*.html'):
  if p.name=='index.html':continue
  s=BeautifulSoup(p.read_text(),'html.parser');h=s.find('h1')
  if not h:continue
  title=h.get_text(' ',strip=True);meta=s.select_one('meta[name="description"]');desc=meta.get('content','') if meta else ''
  image=s.select_one('meta[property="og:image"]');image=image.get('content','') if image else ''
  date=s.select_one('meta[property="article:published_time"]')
  date=date.get('content','') if date else (s.find('time').get('datetime','') if s.find('time') else '')
  article={'title':title,'description':desc,'image':image,'url':'/blog/'+p.stem,'date':date}
  posts.append(article)
  for a in s.select('a[href*="/tag/"]'):
   tag=a['href'].split('/tag/')[-1].strip('/');labels[tag]=a.get_text(' ',strip=True);tags[tag].append(article)
 posts.sort(key=lambda x:(x['date'],x['title']),reverse=True)
 def cards(items):
  html=''
  for post in items:
   img=f'<img loading="lazy" src="{escape(post["image"],quote=True)}" alt="" width="720" height="440">' if post['image'] else ''
   html+=f'<article class="lp-article-card"><a href="{escape(post["url"])}">{img}<div><h2>{escape(post["title"])}</h2><p>{escape(post["description"][:160])}</p><span>Read article ↗</span></div></a></article>'
  return html
 def page(title,items,canonical,pager=''):
  newsletter='<section class="lp-page-section" style="background:#f3f6f9"><div class="lp-container"><p class="lp-eyebrow">Elite Agent newsletter</p><h2 style="font-size:34px">Useful ideas for your next listing.</h2><p style="margin-top:16px">Get agent resources and updates from ListerPros.</p><div class="lp-actions"><a class="lp-button" href="/newsletter">Join the newsletter ↗</a></div></div></section>' if canonical=='/blog/' else ''
  return theme(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | ListerPros</title><link rel="canonical" href="https://listerpros.com{canonical}"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"></head><body><main><section class="lp-page-hero"><div class="lp-container"><p class="lp-eyebrow">Insights for Arizona agents</p><h1>{escape(title)}</h1><p style="margin-top:20px;max-width:650px">Photography, listing preparation and marketing ideas from ListerPros.</p></div></section><section class="lp-page-section"><div class="lp-container"><div class="lp-article-grid">{cards(items)}</div>{pager}</div></section>{newsletter}</main></body></html>''',canonical,True)
 size=12;pages=(len(posts)+size-1)//size
 for index in range(pages):
  links=[]
  if index:links.append(f'<a class="lp-button lp-button-outline" href="/blog/{"" if index==1 else "page/"+str(index)}">← Newer articles</a>')
  if index+1<pages:links.append(f'<a class="lp-button" href="/blog/page/{index+2}">More articles →</a>')
  pager='<nav class="lp-actions" aria-label="Blog pagination">'+''.join(links)+'</nav>'
  target=output/('index.html' if index==0 else f'page/{index+1}/index.html');target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(page('The ListerPros journal',posts[index*size:(index+1)*size],'/blog/' if index==0 else f'/blog/page/{index+1}',pager))
 for tag,items in tags.items():
  target=output/'tag'/tag/'index.html';target.parent.mkdir(parents=True,exist_ok=True)
  unique={p['url']:p for p in items};items=sorted(unique.values(),key=lambda x:(x['date'],x['title']),reverse=True)
  target.write_text(page(labels.get(tag,tag.replace('-',' ')),items,'/blog/tag/'+tag,'<div class="lp-actions"><a class="lp-button lp-button-outline" href="/blog/">All articles ↗</a></div>'))
 return {'posts':len(posts),'tags':len(tags),'archive_pages':pages}
