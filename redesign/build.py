"""Apply the approved Option A design to the current deployed site, preserving page behavior."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,shutil,sys,os,time,hashlib
try:
 import tomllib as tomli
except ImportError:
 import tomli
from patch_offer import patch as patch_offer
from blog_archives import build as build_blog_archives
from refine_pages import refine
from menu_pages import render as render_menu, PAGES as MENU_PAGES
from link_icons import link_icons
from retired_promotions import retire
ROOT=Path(__file__).resolve().parent.parent
R=ROOT/'redesign';LIVE=Path(os.environ.get('LP_SOURCE_DIR',str(R/'live')));DIST=ROOT/'dist';BLOG=Path(os.environ.get('LP_BLOG_SOURCE',str(ROOT.parent/'listerpros-blog-redesign')));BDIST=ROOT/'blog-dist'
BOOK='https://media.listerpros.com/order-forms/ad92f54b-433c-4a6a-8be9-f9a9e9d2d97e'
HEADER=(R/'templates/header.html').read_text();FOOTER=(R/'templates/footer.html').read_text()
VERSION='option-a-20260911'
def asset_url(name):
 source=R/'assets'/name
 version='?v='+hashlib.sha256(source.read_bytes()).hexdigest()[:12] if source.exists() else ''
 return f'/assets/lp/{VERSION}/{name}'+version

MOBILE1=re.compile(r"document\.getElementById\(['\"]mobile-menu-btn['\"]\)(?:\?\.)?\.?addEventListener\(['\"]click['\"],\s*(?:\(\)\s*=>|function\s*\(\))\s*\{\s*document\.getElementById\(['\"]mobile-menu['\"]\)\.classList\.toggle\(['\"]hidden['\"]\);\s*\}\);",re.S)
MOBILE2=re.compile(r"const menuBtn = document\.getElementById\('mobile-menu-btn'\);\s*const mobileMenu = document\.getElementById\('mobile-menu'\);\s*menuBtn\.addEventListener\('click', \(\) => \{\s*mobileMenu\.classList\.toggle\('hidden'\);\s*\}\);",re.S)
def frag(text):return BeautifulSoup(text,'html.parser')
def theme(text,path,blog=False):
 if not blog:text=retire(text,path)
 if not blog and path in MENU_PAGES:text=render_menu(path,text)
 s=frag(text)
 if not s.body or not s.head:return text
 if s.select_one('link[data-lp-theme]'):return text
 # Source page scripts own their interactions; replace only the old navigation handler.
 for t in s.select('script:not([src])'):
  if t.get('type')=='application/ld+json':continue
  code=t.string or t.get_text()
  if 'tailwind.config' in code:t.decompose();continue
  if 'mobile-menu' in code:
   t.string=MOBILE2.sub('',MOBILE1.sub('',code))
 for t in s.select('script[src]'):
  if 'cdn.tailwindcss.com' in t['src']:t.decompose()
 # Remove the floating review badge, retaining in-content testimonials and other widgets.
 for badge in s.select('.elfsight-app-b00b0b7a-0b30-44e6-8dc5-1176817bf95d'):badge.decompose()
 s.body['class']=list(dict.fromkeys(s.body.get('class',[])+['lp-site']))
 nav=None
 for candidate in s.body.find_all(['nav','header'],recursive=False):
  if candidate.find('a') and (candidate.find('img') or candidate.get('class')==['nav']):nav=candidate;break
 if nav:nav.replace_with(frag(HEADER))
 else:s.body.insert(0,frag(HEADER))
 oldfoot=s.body.find('footer',recursive=False)
 if oldfoot:oldfoot.replace_with(frag(FOOTER))
 else:s.body.append(frag(FOOTER))
 main=s.select_one('main')
 if main:
  # Preserve the existing IDs used by forms and scripts.
  if not main.get('id'):main['id']='lp-main'
  else:
   marker=s.new_tag('span',id='lp-main');main.insert(0,marker)
 else:
  h=s.find('h1')
  if h:
   marker=s.new_tag('span',id='lp-main');h.insert_before(marker)
 # Plain section heroes become the shared dark introductory block. Never recolor a whole form or gallery.
 h1=s.find('h1')
 if h1:
  region=h1.find_parent(['section','header'])
  if not s.body.get('data-lp-menu-refresh') and region and 'lp-header' not in region.get('class',[]) and not region.find('form') and not region.find('h2'):
   region['class']=region.get('class',[])+['lp-page-hero']
  h1['class']=h1.get('class',[])+['lp-page-title']
 for el in s.select('section.sticky'):
  el['class']=el.get('class',[])+['lp-page-subnav']
 for el in s.select('.rounded-2xl,.rounded-xl'):
  if el.name in ['article'] or (el.name=='div' and 'border' in el.get('class',[]) and 'fixed' not in el.get('class',[])):
   el['class']=el.get('class',[])+['lp-card']
 # Keep internal visits on the redesigned domain; preserve fragments and query strings.
 for a in s.select('a[href]'):
  a['href']=re.sub(r'^https?://(?:www\.)?listerpros\.com(?=/|$)','',a['href']) or '/'
  if a.get('href')=='#' and a.get_text(strip=True).lower() in ['book now','book a shoot']:a['href']=BOOK
 # Root-relative local image URLs prevent nested guide/campaign pages from losing assets.
 for tag,attr in [('img','src'),('link','href')]:
  for el in s.select(f'{tag}[{attr}]'):
   u=el[attr]
   if u.startswith('images/'):
    el[attr]=('/blog/' if blog and (BLOG/u).exists() else '/')+u
 s=refine(s,path,blog)
 for href in [asset_url('utilities.css'),asset_url('site.css')]:
  link=s.new_tag('link',rel='stylesheet',href=href);link['data-lp-theme']='';s.head.append(link)
 script=s.new_tag('script',src=asset_url('site.js'));script['defer']='';s.body.append(script)
 if s.body.get('data-lp-page')=='community-library':
  s.head.append(s.new_tag('link',rel='stylesheet',href=asset_url('library.css')))
  extra=s.new_tag('script',src=asset_url('library.js'));extra['defer']='';s.body.append(extra)
 if s.body.get('data-lp-menu-refresh'):
  s.head.append(s.new_tag('link',rel='stylesheet',href=asset_url('menu.css')))
  extra=s.new_tag('script',src=asset_url('menu.js'));extra['defer']='';s.body.append(extra)
 return str(link_icons(s))
def home():
 live=frag((LIVE/'index.html').read_text());proposal=frag((R/'templates/home-option-a.html').read_text())
 main=proposal.find('main');main['class']=['lp-home'];main['id']='lp-main'
 # Keep the approved A direction compact: hero, route strip, reviews, work, packages, community, FAQ, team CTA.
 keep=[]
 for el in list(main.children):
  if not getattr(el,'name',None):continue
  classes=el.get('class',[])
  if el.get('id')=='experience':el.decompose();continue
  if el.select_one('.first-shoot'):el.decompose();continue
  if el.select_one('.steps'):
   team=el.select_one('.team-panel')
   if team:keep.append(str(team))
   el.decompose()
 hero=main.select_one('.a-hero');hero.h1.clear();hero.h1.append(frag('Media that Sells<br>Homes <span>Faster</span>'))
 hero.select_one('.lead').string='Professional photos, video, drone and 3D tours for Arizona agents. An experienced local team, easy booking and customer care that keeps you coming back.'
 secondary=hero.select_one('.actions .secondary');secondary.string='View pricing';secondary['href']='/pricing'
 # Keep the Google review proof immediately beneath the booking/pricing choices.
 proof=hero.select_one('.hero-proof');proof.clear()
 proof.append(frag('<a class="lp-google-proof" href="/testimonials"><span class="lp-stars" aria-label="5 out of 5 stars">★★★★★</span> <strong>5.0</strong> <span>from 400+ Google reviews ↗</span></a><span>Arizona owned since 2013</span>'))
 hero.select_one('.actions').insert_after(proof.extract())
 coverage=main.select('.entry-strip .wrap > div')[1]
 coverage.select_one('strong').string='Serving Arizona since 2013'
 coverage.select_one('span').string='Local experience. Statewide service.'
 reviews=main.select_one('#reviews')
 reviews.select_one('.eyebrow').string='Google reviews'
 reviews.h2.string='Trusted by Arizona agents.'
 # Review cards carry the evidence without repeating all of the hero statistics.
 reviews.select_one('.proof-band').decompose()
 reviews.select_one('.fine').string='Excerpts from ListerPros agent reviews.'
 heading=main.select_one('#pricing h2');heading.clear();heading.append(frag('Start with what<br>your listing <strong>needs.</strong>'))
 for answer in main.select('.faq details'):
  if answer.summary and 'my area' in answer.summary.get_text():
   answer.p.clear();answer.p.append(frag('We serve agents across Arizona, including Sedona, Flagstaff, Prescott and beyond. Enter your listing address during booking to confirm availability and the final price, or <a class="text-link" href="/arizona-real-estate-photography">explore service areas</a>.'))

 main.select_one('.entry-strip a[href="#teams"]')['href']='/teams'
 for a in main.select('a[href]'):
  a['href']=re.sub(r'^https?://(?:www\.)?listerpros\.com(?=/|$)','',a['href']) or '/'
  if a['href']=='#pricing':a['href']='/pricing'
  if a['href']=='#teams':a['href']='/teams'
 for img in main.select('img[src^="assets/"]'):
  name=img['src'].split('/')[-1]
  img['src']='/assets/lp/'+VERSION+'/'+name
 # Replace preview buttons with genuine booking links. No mockup dialog or extra booking gate.
 for b in main.select('[data-book]'):
  a=proposal.new_tag('a',href=BOOK);a['class']=b.get('class',[])
  for child in list(b.contents):a.append(child.extract())
  if 'Try' in a.get_text():a.clear();a.append('Book your shoot ↗')
  b.replace_with(a)
 # Dedicated team section replaces the removed process block, and gets a real page.
 team=frag('<section class="section"><div class="wrap"><div class="team-panel" id="teams"><div><div class="eyebrow" style="color:#79bfff">Teams & brokerages</div><h3>Your whole team.<br>A consistent first impression.</h3><p>Let’s talk about your listings, service areas and media needs.</p></div><a class="btn" href="/teams">Tell us about your team ↗</a></div></div></section>')
 close=main.select_one('.closing');close.insert_before(team)
 # Clear review footnotes from the homepage strip; keep precise testimonial attribution in the review block.
 html='<!doctype html><html lang="en">'+str(live.head)+'<body>'+HEADER+str(main)+FOOTER
 # Retain current analytics in head, attribution capture and the existing intent-aware offer script.
 for t in live.select('body>script'):
  if 'lp-offer.js' in t.get('src','') or 'LP click-id capture' in t.get_text():html+=str(t)
 html+='</body></html>'
 s=frag(html)
 for t in s.select('script'):
  if 'cdn.tailwindcss.com' in t.get('src','') or 'tailwind.config' in t.get_text():t.decompose()
 for meta in s.select('meta[name="description"],meta[property="og:description"],meta[name="twitter:description"]'):
  meta['content']='Professional real estate photography, video, drone and 3D tours for Arizona agents. Five-hour standard photo delivery. Book your shoot with ListerPros.'
 s.body['class']=['lp-site']
 for name in ['utilities.css','site.css','home.css']:
  link=s.new_tag('link',rel='stylesheet',href=asset_url(name));link['data-lp-theme']='';s.head.append(link)
 for t in s.select('style'):t.decompose()
 script=s.new_tag('script',src=asset_url('site.js'));script['defer']='';s.body.append(script)
 return str(link_icons(s))
def teams():
 return theme((R/'templates/teams.html').read_text(),'teams.html')
def teams_thanks():
 return theme((R/'templates/teams-thanks.html').read_text(),'teams-thanks.html')
def write_config():
 config=tomli.loads((LIVE/'netlify.toml').read_text());blog_url=os.environ.get('LP_BLOG_TARGET','https://listerpros-blog.netlify.app')
 lines=['[build]','publish = "dist"','','[functions]','directory = "redesign/functions"','']
 def emit_obj(prefix,obj):
  lines.append('['+prefix+']')
  for k,v in obj.items():lines.append(json.dumps(k)+' = '+json.dumps(v))
  lines.append('')
 for r in config.get('redirects',[]):
  lines.append('[[redirects]]')
  for k,v in r.items():
   if isinstance(v,dict):continue
   if k=='to' and r.get('from','').startswith('/blog'):v=v.replace('https://listerpros-blog.netlify.app',blog_url)
   lines.append(k+' = '+json.dumps(v))
  lines.append('')
  for k,v in r.items():
   if isinstance(v,dict) and v:emit_obj('redirects.'+k,v)
 for h in config.get('headers',[]):
  lines+=['[[headers]]','for = '+json.dumps(h['for']),''];emit_obj('headers.values',h['values'])
 for route in ['/redesign/*','/netlify/*','/package.json','/package-lock.json','/node_modules/*','/claude.md']:
  lines+=['[[redirects]]','from = '+json.dumps(route),'to = "/404.html"','status = 404','force = true','']
 # Draft-only indexing controls live in the publish folder; production keeps canonical metadata.
 (ROOT/'netlify.toml').write_text('\n'.join(lines))
def run():
 start=time.time()
 for folder in [DIST,BDIST]:
  if folder.exists():shutil.rmtree(folder)
  folder.mkdir()
 reports=[]
 for p in LIVE.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(LIVE)
  if rel.parts[0] in ['scripts','netlify','reports','citations'] or rel.name in ['netlify.toml','package.json','package-lock.json']:continue
  out=DIST/rel;out.parent.mkdir(parents=True,exist_ok=True)
  if p.suffix=='.html':
   out.write_text(home() if rel.as_posix()=='index.html' else theme(p.read_text(),str(rel)))
   reports.append(str(rel))
  else:shutil.copy2(p,out)
  if len(reports) and len(reports)%300==0 and p.suffix=='.html':print('Styled',len(reports),'site pages',flush=True)
 (DIST/'teams.html').write_text(teams())
 (DIST/'teams-thanks.html').write_text(teams_thanks())
 sitemap=DIST/'sitemap.xml'
 if sitemap.exists() and 'https://listerpros.com/teams<' not in sitemap.read_text():
  sitemap.write_text(sitemap.read_text().replace('</urlset>','<url><loc>https://listerpros.com/teams</loc></url></urlset>'))
 (DIST/'404.html').write_text(theme('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found | ListerPros</title></head><body><main class="lp-page-section"><div class="lp-container"><h1>Let’s get you to the right place.</h1><p style="margin:25px 0">This page isn’t available. Explore pricing, find your community or book your next shoot.</p><div class="lp-actions"><a class="lp-button" href="/">Back to ListerPros</a><a class="lp-button lp-button-outline" href="/pricing">View pricing</a></div></div></main></body></html>','404.html'))
 assets=DIST/'assets/lp'/VERSION;assets.mkdir(parents=True,exist_ok=True)
 for p in (R/'assets').iterdir():shutil.copy2(p,assets/p.name)
 # Blog remains a separate site, with the same shell and assets when proxied under /blog.
 blogpages=[]
 for p in ([] if os.environ.get('LP_SKIP_BLOG')=='1' else BLOG.glob('*.html')):
  (BDIST/p.name).write_text(theme(p.read_text(),str(p.name),True));blogpages.append(p.name)
 if os.environ.get('LP_SKIP_BLOG')!='1' and (BLOG/'images').exists():shutil.copytree(BLOG/'images',BDIST/'images',dirs_exist_ok=True)
 archive_stats={} if os.environ.get('LP_SKIP_BLOG')=='1' else build_blog_archives(BLOG,BDIST,theme)
 (R/'blog-archive-report.json').write_text(json.dumps(archive_stats,indent=2))
 (BDIST/'netlify.toml').write_text((R/'templates/blog-netlify.toml').read_text())
 shutil.copytree(assets,BDIST/'assets/lp'/VERSION,dirs_exist_ok=True)
 fdir=R/'functions'
 if fdir.exists():shutil.rmtree(fdir)
 shutil.copytree(LIVE/'netlify/functions',fdir,dirs_exist_ok=True)
 write_config()
 patch_offer(DIST/'js/lp-offer.js')
 case_map={'/'+p.relative_to(DIST).as_posix():p for p in DIST.rglob('*') if p.is_file() and p.suffix.lower() not in ['.html','.json','.js']}
 lookup={k.lower():k for k in case_map}
 for folder in [DIST,BDIST]:
  for page in folder.rglob('*.html'):
   text=page.read_text()
   text=re.sub(r'(?:(?:https?://(?:www\.)?listerpros\.com))?(/images/[^\s\"\'<>]+)',lambda m:('https://listerpros.com' if m.group(0).startswith('http') else '')+lookup.get(m.group(1).lower(),m.group(1)),text)
   page.write_text(text)
 # Restrict indexing of review deployments without changing production canonical tags.
 for d in [DIST,BDIST]:
  if os.environ.get('LP_PRODUCTION')=='1':(d/'_headers').unlink(missing_ok=True)
  else:(d/'_headers').write_text('/*\n  X-Robots-Tag: noindex, nofollow\n')
 (R/'build-report.json').write_text(json.dumps({'main_pages':len(reports)+3,'blog_pages':len(blogpages),'main_paths':reports+['teams.html','teams-thanks.html','404.html'],'blog_paths':blogpages,'seconds':round(time.time()-start)},indent=2))
 print('Built',len(reports)+3,'main pages +',len(blogpages),'blog pages in',round(time.time()-start),'seconds',flush=True)
if __name__=='__main__':run()
