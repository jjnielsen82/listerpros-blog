"""Keep old campaign links useful after their advertised promotion expires."""
from bs4 import BeautifulSoup
PATHS={'refer.html','r/index.html'}
def retire(text,path):
 if path not in PATHS:return text
 s=BeautifulSoup(text,'html.parser')
 if s.title:s.title.string='Referrals | ListerPros'
 desc=s.select_one('meta[name="description"]')
 if desc:desc['content']='Contact the ListerPros team for current referral options, or explore today’s listing media packages.'
 s.body.clear()
 s.body.append(BeautifulSoup('''<main><section class="lp-page-hero"><div class="lp-container lp-plain-intro"><p class="lp-eyebrow">ListerPros referrals</p><h1>Thanks for sharing ListerPros.</h1><p>The summer referral promotion ended August 31. If you received an older offer or want to refer another agent, our admin team can help with current options.</p><div class="lp-actions"><a class="lp-button" href="mailto:info@listerpros.com?subject=ListerPros%20referral%20question">Ask about referrals</a><a class="lp-button lp-button-outline" href="/pricing">View current pricing</a></div></div></section><section class="lp-page-section"><div class="lp-container"><h2>Have a question about a previous referral?</h2><p>Contact our team at <a href="tel:4805827767">480.582.7767</a> or <a href="mailto:info@listerpros.com">info@listerpros.com</a>. We can help check the status of a referral or an existing credit.</p></div></section></main>''','html.parser'))
 return str(s)
