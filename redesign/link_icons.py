"""Decorative SVG link arrows cannot switch to emoji on mobile platforms."""
import re
from bs4 import NavigableString

ARROW=re.compile(r'[↗→](?:\ufe0e|\ufe0f)?')
def link_icons(s):
 for text in list(s.find_all(string=ARROW)):
  if not text.find_parent(['a','button']) or text.find_parent(['script','style','svg']):continue
  value=str(text);last=0
  for match in ARROW.finditer(value):
   if match.start()>last:text.insert_before(NavigableString(value[last:match.start()]))
   icon=s.new_tag('svg',attrs={'class':'lp-link-arrow','width':'14','height':'14','viewBox':'0 0 16 16','fill':'none','stroke':'currentColor','stroke-width':'1.7','aria-hidden':'true','focusable':'false','style':'display:inline-block;vertical-align:-.12em;flex-shrink:0'})
   path='M4 12 12 4M4 4h8v8' if match[0][0]=='↗' else 'M3 8h10M8 3l5 5-5 5'
   icon.append(s.new_tag('path',attrs={'d':path,'stroke-linecap':'round','stroke-linejoin':'round'}));text.insert_before(icon);last=match.end()
  if last<len(value):text.insert_before(NavigableString(value[last:]))
  text.extract()
 return s
