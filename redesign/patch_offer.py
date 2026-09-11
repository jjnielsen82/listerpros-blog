from pathlib import Path

def patch(path):
 s=path.read_text()
 s=s.replace("document.removeEventListener('keydown', box._esc);", "document.removeEventListener('keydown', box._esc);\n    document.body.style.overflow = box._previousOverflow || '';\n    if (box._returnFocus && box._returnFocus.isConnected) box._returnFocus.focus();")
 s=s.replace("box._offer = offer.name;", "box._offer = offer.name;\n    box._returnFocus = document.activeElement;\n    box._previousOverflow = document.body.style.overflow;\n    document.body.style.overflow = 'hidden';")
 s=s.replace("box._esc = function (e) { if (e.key === 'Escape') close(box, 'dismiss'); };", """box._esc = function (e) {
      if (e.key === 'Escape') close(box, 'dismiss');
      if (e.key === 'Tab') {
        var items = Array.from(box.querySelectorAll('button:not([disabled]), a[href], input:not([type="hidden"]):not([tabindex="-1"])')).filter(function (el) { return !el.hidden; });
        var first = items[0], last = items[items.length - 1];
        if (e.shiftKey && (document.activeElement === first || !box.contains(document.activeElement))) { e.preventDefault(); last && last.focus(); }
        else if (!e.shiftKey && (document.activeElement === last || !box.contains(document.activeElement))) { e.preventDefault(); first && first.focus(); }
      }
    };""")
 s=s.replace("'<h2>' + offer.okTitle + '</h2>'", "'<h2 id=\"lpo-t\" tabindex=\"-1\">' + offer.okTitle + '</h2>'")
 s=s.replace("'<div class=\"lpo-code\">' + code + '</div>'", "'<div class=\"lpo-code\"></div>'")
 marker="card.querySelector('.lpo-x').addEventListener('click', function () { close(box); });"
 s=s.replace(marker, "if (card.querySelector('.lpo-code')) card.querySelector('.lpo-code').textContent = code;\n          card.querySelector('#lpo-t').focus();\n          "+marker)
 path.write_text(s)
if __name__=='__main__':patch(Path('dist/js/lp-offer.js'))
