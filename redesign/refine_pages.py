"""Page-family layouts and explicit surface contrast for the approved site design."""
from bs4 import BeautifulSoup
from pathlib import PurePosixPath
import re
from library_pages import refine_library
BOOK='https://media.listerpros.com/order-forms/ad92f54b-433c-4a6a-8be9-f9a9e9d2d97e'

def add(el,*classes):
 if el:el['class']=list(dict.fromkeys(el.get('class',[])+list(classes)))
def family(path,blog=False):
 if blog:
  blogpath=path.removeprefix('/blog/').lstrip('/')
  return 'blog-index' if blogpath in ['', 'index.html'] or blogpath.startswith(('page/','tag/')) else 'blog-article'
 stem=PurePosixPath(path).stem
 if path.startswith('community-photos/'):
  return 'community-library' if len(PurePosixPath(path).parts)<=3 else 'community-gallery'
 if stem.endswith('-real-estate-photography'):return 'location'
 if stem in ['resources','guides']:return 'resources'
 if stem in ['help-center','shoot-prep']:return 'help'
 if stem in ['terms-of-service']:return 'policies'
 if stem in ['newsletter','playbook','guide-kit'] or stem.endswith(('-playbook','-guide')):return 'download'
 if stem in ['free-community-photos','refer','free-shirt']:return 'request'
 if stem in ['pricing','why','about','portfolio','testimonials','teams','teams-thanks']:return stem
 return 'campaign'

def fragment(html):return BeautifulSoup(html,'html.parser')
def refine(s,path,blog=False):
 kind=family(path,blog);s.body['data-lp-page']=kind
 if kind=='community-library':s=refine_library(s,path)
 if kind=='community-gallery':
  for script in s.select('script:not([src])'):
   if 'Enter your listing address above to download' in script.get_text():
    script.string=script.get_text().replace('Enter your listing address above to download','Enter the email on your listings above to request access to')
 if s.body.get('data-lp-menu-refresh'):return s
 # Remove repeated guide advertisements appended to unrelated conversion pages.
 if kind not in ['resources','download','blog-index','blog-article']:
  for h in list(s.select('h2')):
   if '23 free guides, starting with' in h.get_text(' ',strip=True):
    block=h.find_parent('section')
    if block and not block.find('form') and not block.get('id'):block.decompose()
 h1=s.find('h1')
 if not h1:return s
 # A catalog is not a hero: keep its cards on a light surface and isolate its introduction.
 if kind=='resources' and path=='guides.html':
  old=h1.find_parent('section');old['class']=[c for c in old.get('class',[]) if c!='lp-page-hero'];add(old,'lp-resource-catalog')
  intro=h1.parent;intro.extract()
  hero=fragment('<section class="lp-page-hero lp-catalog-hero"><div class="lp-container"></div></section>').section
  hero.div.append(intro);old.insert_before(hero)
 # Replace inherited location-page collages and dense copy with a deliberate split layout.
 if kind=='location':
  old=h1.find_parent('section');place=h1.get_text(' ',strip=True).replace('Real Estate Photography','').strip() or 'Arizona'
  legacy_intro=old.find('p').get_text(' ',strip=True) if old and old.find('p') else ''
  hero=fragment(f'''<section class="lp-page-hero lp-location-hero"><div class="lp-container lp-location-grid"><div><p class="lp-eyebrow">Serving Arizona since 2013</p><h1>{place} Real Estate<br><span class="gradient-text">Photography</span></h1><p class="lp-location-lead">Professional photos, video, drone and 3D tours for {place} listings. Easy online booking and a local team that cares about your experience.</p><div class="lp-actions"><a class="lp-button" href="{BOOK}">Book your shoot ↗</a><a class="lp-button lp-button-outline" href="/pricing">View pricing</a></div><p class="lp-delivery-note">Standard photos delivered within 5 hours. <a href="/help-center#delivery">Delivery details</a></p><div class="lp-location-proof"><div><strong>5,000+</strong><span>Agents served</span></div><div><strong>150K+</strong><span>Listings photographed</span></div><a href="/testimonials"><strong>5.0 <span class="lp-proof-star" aria-hidden="true">★</span></strong><span>400+ Google reviews ↗</span></a></div></div><figure><img src="/assets/lp/option-a-20260911/hero.jpg" alt="Arizona listing photography by ListerPros" width="1600" height="1067" fetchpriority="high"><figcaption>Real listings. Our real work. <a href="/portfolio">View the portfolio ↗</a></figcaption></figure></div></section>''').section
  # Keep every pre-existing anchor in the replaced introductory region.
  for el in old.select('[id]'):
   mark=s.new_tag('span',id=el['id']);hero.insert(0,mark)
  if old.get('id'):hero['id']=old['id']
  old.replace_with(hero)
  if legacy_intro:
   legacy_intro=legacy_intro.replace('all delivered in 5 hours','standard photos delivered within 5 hours; other media have separate delivery times')
   local=s.new_tag('section',attrs={'class':['lp-local-context']});wrap=s.new_tag('div',attrs={'class':['lp-container']});heading=s.new_tag('h2');heading.string=f'Your {place} listings. Our Arizona team.';p=s.new_tag('p');p.string=legacy_intro;wrap.extend([heading,p]);local.append(wrap)
   # Local detail belongs below the service gallery, not in the first-screen pitch.
   next_section=hero.find_next_sibling('section')
   if next_section:next_section.insert_after(local)
   else:hero.insert_after(local)
  h1=hero.h1
 if kind=='testimonials':
  if s.title:s.title.string='ListerPros Reviews — Arizona Real Estate Agents'
  for meta in s.select('meta[property="og:title"]'):meta['content']='ListerPros Reviews — Arizona Real Estate Agents'
  for el in s.select('div'):
   if el.string and el.string.strip()=='390+':el.string='400+'
   elif el.string and 'Google Reviews' in el.string and '4.9' in el.string:el.string='Google reviews'
 if kind=='why':
  h1.clear();h1.append(fragment('Great media.<br>A team you can rely on.'))
  container=h1.parent
  badge=container.find('span',recursive=False)
  if badge:badge.string='The ListerPros experience';badge['class']=['lp-eyebrow']
  p=container.find('p',recursive=False)
  if p:p.string='Your next listing deserves professional media, clear communication and people who care. Try one shoot and experience ListerPros for yourself.'
 # Lift the introduction out of long community lists; keep search, unlock and download logic intact.
 if kind in ['community-library','community-gallery']:
  intro=h1.parent
  add(intro,'lp-library-intro')
  main=s.find('main');add(main,'lp-library-main')
  if main:
   wrap=main.find('div',recursive=False);add(wrap,'lp-library-container')
  if kind=='community-library':
   add(intro,'lp-library-banner')
   for a in main.select('a[href]') if main else []:
    if 'community-photos/' in a['href'] and a.find(['h2','h3']):add(a,'lp-directory-card')
   for inp in s.select('input#filter'):add(inp,'lp-library-search')
  else:
   add(intro.parent,'lp-gallery-heading')
   for a in s.select('a[download]'):add(a,'lp-download-action')
 # Form pages use a readable editorial column and a light, clearly bounded form card.
 if kind in ['download','request']:
  intro=h1.parent;add(intro,'lp-form-intro-column')
  section=h1.find_parent('section')
  if section:add(section,'lp-form-page')
  for f in s.select('form'):
   if f.find_parent(['footer','nav']):continue
   add(f,'lp-customer-form')
   ancestor=f.find_parent('div',class_=lambda c:c and ('bg-white' in c.split()))
   if ancestor:add(ancestor,'lp-form-panel')
 if kind=='resources':
  for a in s.select('a[href]'):
   if a.find(['h2','h3']) and not a.find_parent(['header','footer']):add(a,'lp-resource-card')
 if kind=='portfolio':
  add(s.select_one('#portfolio-grid'),'lp-portfolio-gallery')
 if kind=='blog-article':
  article=s.find('article')
  if article:add(article,'lp-article-body')
 # Attach appearance classes without changing IDs, names, actions or script-owned classes.
 for el in s.select('section,main>div,body>div'):
  if el.find_parent(['header','footer']) or el.get('id') in ['lightbox']:continue
  if el.name=='section' and 'lp-page-hero' not in el.get('class',[]):add(el,'lp-content-section')
 for a in s.select('a,button'):
  if a.find_parent(['header','footer']) or a.find('img'):continue
  cs=a.get('class',[])
  if 'lp-button' in cs or 'btn' in cs:continue
  if ('rounded-full' in cs and any(c.startswith(('px-6','px-8','px-10')) for c in cs)) or ('bg-primary' in cs and any(c.startswith(('px-6','px-8')) for c in cs)):
   if a.name=='button' and ('filter-btn' in cs or 'size-btn' in cs):continue
   add(a,'lp-content-button')
   if 'bg-primary' in cs or 'bg-blue-600' in cs:add(a,'lp-content-primary')
 # Identify actual dark/light surfaces before fixing text. White cards inside heroes stay dark-on-white.
 for el in s.select('section,div,article,aside,figure,a,button,input,select,textarea'):
  if el.find_parent(['header','footer']):continue
  cs=el.get('class',[])
  dark=any(c in ['from-primary','from-secondary','from-blue-600','from-blue-700','bg-primary','lp-library-banner','lp-page-hero','bg-dark','bg-gray-950','bg-gray-900','bg-slate-900','bg-slate-950','from-gray-950'] for c in cs)
  if el.name=='section' and any(c in ['bg-primary','bg-blue-600','bg-blue-700','from-green-500'] for c in cs):dark=True
  light=any(c in ['bg-white','bg-gray-50','bg-gray-100','bg-blue-50','bg-slate-50','bg-green-50','bg-amber-50'] for c in cs)
  if 'lp-page-hero' in cs:light=False
  if el.name in ['input','select','textarea']:light=True;dark=False
  if dark:add(el,'lp-surface-dark')
  elif light:add(el,'lp-surface-light')
 for el in s.select('h1,h2,h3,h4,p,span,strong,small,div,a,label,li'):
  if el.find_parent(['header','footer']):continue
  cs=el.get('class',[])
  surface=next((a for a in [el]+list(el.parents) if getattr(a,'attrs',None) and any(c in a.get('class',[]) for c in ['lp-surface-dark','lp-surface-light'])),None)
  if not surface:continue
  if 'lp-surface-dark' in surface.get('class',[]):
   if any(c in ['text-dark','text-gray-900','text-gray-800','text-gray-700','text-black'] for c in cs):add(el,'lp-on-dark')
   if any(c in ['text-gray-600','text-gray-500','text-gray-400','text-white/60','text-white/50'] for c in cs):add(el,'lp-on-dark-muted')
  elif any(c in ['text-white','text-white/80'] for c in cs) and el.name not in ['a','button'] and not el.find_parent('a'):
   add(el,'lp-on-light')
 # No oversized headings or tiny inline links on long answers and policy pages.
 for el in s.select('details'):add(el,'lp-answer')
 return s
