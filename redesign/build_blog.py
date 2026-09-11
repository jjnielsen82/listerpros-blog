"""Blog-only build used on Netlify after each automated article publish."""
from pathlib import Path
import shutil,os
os.environ['LP_BLOG_SOURCE']=str(Path(__file__).resolve().parent.parent)
from build import theme,VERSION,R
from blog_archives import build as archives
ROOT=R.parent;OUT=ROOT/'blog-dist'
OUT.mkdir(exist_ok=True)
for p in ROOT.glob('*.html'):(OUT/p.name).write_text(theme(p.read_text(),p.name,True))
archives(ROOT,OUT,theme)
for name in ['images']:
 if (ROOT/name).exists():shutil.copytree(ROOT/name,OUT/name,dirs_exist_ok=True)
shutil.copytree(R/'assets',OUT/'assets/lp'/VERSION,dirs_exist_ok=True)
for name in ['robots.txt','sitemap.xml']:
 if (ROOT/name).exists():shutil.copy2(ROOT/name,OUT/name)
shutil.copy2(R/'templates/blog-netlify.toml',OUT/'netlify.toml')
(OUT/'_headers').unlink(missing_ok=True)
print('Built',len(list(OUT.rglob('*.html'))),'styled blog pages')
