#!/usr/bin/env python3
"""Builds sgci-niger.com from its sources.

  src/index.html            bilingual source of the home page (markup + the I18N dictionary)
  content/articles/*.json   news articles (status "published" or "draft")
  ->  index.html (/), en/index.html (/en), ar/index.html (/ar)
      actualites/<slug>.html, en/news/<slug>.html, mentions-legales.html, en/legal-notice.html,
      404.html, sitemap.xml

Run:  python3 scripts/build_site.py            (published articles only)
      python3 scripts/build_site.py --drafts   (also shows drafts, for previews)
Edit src/index.html and content/, never the generated files. Standard library only.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://www.sgci-niger.com"
DRAFTS = "--drafts" in sys.argv
HOME = {"fr": "/", "en": "/en", "ar": "/ar"}
OUT = {"fr": "index.html", "en": "en/index.html", "ar": "ar/index.html"}
TITLE = {"fr": "SGCI — Mine d'or AMZEGUER, Niger | Société minière",
         "en": "SGCI — AMZEGUER gold mine, Niger | Mining company",
         "ar": "SGCI — منجم ذهب أمزقر، النيجر"}
OGT = {"fr": "SGCI — Mine d'or AMZEGUER, Niger", "en": "SGCI — AMZEGUER gold mine, Niger", "ar": "SGCI — منجم ذهب أمزقر، النيجر"}
LOCALE = {"fr": "fr_FR", "en": "en_US", "ar": "ar_AR"}
FLAG = {"fr": ("0 0 24 16", "#flag-fr-src"), "en": ("0 0 60 30", "#flag-gb-src"), "ar": ("0 0 24 16", "#flag-sa-src")}
LEGAL = {"fr": "/mentions-legales", "en": "/en/legal-notice", "ar": "/en/legal-notice"}
MONTHS = {"fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
          "en": "January February March April May June July August September October November December".split()}
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%230B2545'/%3E"
           "%3Crect x='9' y='9' width='46' height='46' fill='none' stroke='%23c8a24b' stroke-width='3'/%3E"
           "%3Ctext x='32' y='44' text-anchor='middle' font-family='Georgia,serif' font-size='34' font-weight='600' fill='%23c8a24b'%3ES%3C/text%3E%3C/svg%3E")
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com" />\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
         '<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..600&family=Manrope:wght@300..700&display=swap" rel="stylesheet" />')
ORG = {"@context": "https://schema.org", "@type": "Organization", "name": "SGCI SARLU",
       "legalName": "Société Générale de Commerce et de l'Industrie SARLU", "url": BASE,
       "email": "contact@sgci-niger.com", "telephone": "+227 90 50 53 50",
       "address": {"@type": "PostalAddress", "addressLocality": "Agadez", "addressCountry": "NE"}}

esc = lambda t: html.escape(t, quote=False)
att = lambda t: html.escape(t, quote=True)
ld = lambda d: json.dumps(d, ensure_ascii=False, separators=(",", ":"))


def sub1(pattern, repl, text, flags=re.S):
    new, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=flags)
    assert n == 1, "pattern not found: " + pattern
    return new


def load_i18n(src):
    raw = src[src.index("const I18N = ") + len("const I18N = "):src.index("\n};\n\nconst FLAG") + 2]
    raw = re.sub(r"^(\s*)(fr|en|ar):\{", r'\1"\2":{', raw, flags=re.M)
    raw = re.sub(r",(\s*[}\]])", r"\1", raw)
    return json.loads(raw)


def fmt_date(iso, lang):
    if not iso:
        return ""
    y, m, d = (int(x) for x in iso.split("-"))
    if lang == "ar":
        return "%02d/%02d/%d" % (d, m, y)
    mo = MONTHS[lang][m - 1]
    return ("%d %s %d" % (d, mo, y)) if lang == "en" else ("%s %s %d" % ("1er" if d == 1 else d, mo, y))


def load_articles():
    arts = []
    for f in sorted((ROOT / "content" / "articles").glob("*.json")):
        a = json.loads(f.read_text(encoding="utf-8"))
        if a.get("status") == "published" or (DRAFTS and a.get("status") == "draft"):
            arts.append(a)
    arts.sort(key=lambda a: (a.get("date") or "9999", -a.get("order", 0)), reverse=True)
    return arts


def art_lang(a, lang):
    """Language actually used for an article on a page in `lang` (falls back to English, then French)."""
    for l in (lang, "en", "fr"):
        if l in a:
            return l


def art_url(a, lang):
    return ("/en/news/%s" if lang == "en" else "/actualites/%s") % a["slug"]


def news_section(arts, lang, d):
    cards = []
    for i, a in enumerate(arts):
        l = art_lang(a, lang)
        t, url = a[l], art_url(a, l)
        meta = " · ".join(x for x in (t.get("category", ""), fmt_date(a.get("date"), lang)) if x)
        cards.append(
            '      <article class="news-card%s reveal">\n'
            '        <a class="news-img" href="%s" tabindex="-1" aria-hidden="true"><img src="%s" alt="" loading="lazy" decoding="async" width="1020" height="765" /></a>\n'
            '        <div class="news-body">\n          <div class="opp-ref">%s</div>\n          <h3><a href="%s">%s</a></h3>\n          <p>%s</p>\n'
            '          <a class="news-more" href="%s">%s</a>\n        </div>\n      </article>'
            % (" feature" if i == 0 else "", url, a["cover"], esc(meta), url, esc(t["title"]), esc(t["lead"]), url, esc(d["news.read"])))
    return ('<!-- ===== NEWS ===== -->\n<section id="news" class="news">\n  <div class="wrap">\n    <div class="reveal" style="max-width:760px">\n'
            '      <div class="sec-eyebrow" data-i18n="news.eyebrow">%s</div>\n      <h2 class="sec-title" data-i18n="news.title">%s</h2>\n'
            '      <p class="lead-2" data-i18n="news.intro">%s</p>\n    </div>\n    <div class="news-grid">\n%s\n    </div>\n  </div>\n</section>\n\n'
            % (esc(d["news.eyebrow"]), esc(d["news.title"]), esc(d["news.intro"]), "\n".join(cards)))


def build_home(src, i18n, arts, lang):
    d, page = i18n[lang], src
    # news block and menu entry (only when at least one article is shown)
    page = page.replace("<!-- NEWS:SECTION -->\n", news_section(arts, lang, d) if arts else "", 1)
    page = page.replace("      <!-- NEWS:NAV -->\n", '      <li><a href="#news" data-i18n="nav.news">%s</a></li>\n' % esc(d["nav.news"]) if arts else "", 1)

    # texts: every data-i18n element gets its translation written into the markup
    def txt(m):
        k = m.group(3)
        return m.group(1) + (esc(d[k]) if k in d else m.group(4)) + m.group(5)
    page, n = re.subn(r'(<([a-zA-Z0-9]+)\b[^>]*\bdata-i18n="([^"]+)"[^>]*>)([^<]*)(</\2>)', txt, page)
    assert n == len(re.findall(r'\bdata-i18n="', page)), "a data-i18n element contains markup"
    page = re.sub(r'(<([a-zA-Z0-9]+)\b[^>]*\bdata-i18n-html="([^"]+)"[^>]*>)(.*?)(</\2>)',
                  lambda m: m.group(1) + d.get(m.group(3), m.group(4)) + m.group(5), page, flags=re.S)
    page = re.sub(r'placeholder="[^"]*"( data-i18n-ph="([^"]+)")',
                  lambda m: 'placeholder="%s"%s' % (att(d.get(m.group(2), "")), m.group(1)), page)

    # document language and switcher state, fixed in the markup
    page = sub1(r'<html lang="fr" dir="ltr">', '<html lang="%s" dir="%s">' % (lang, "rtl" if lang == "ar" else "ltr"), page)
    page = sub1(r'<span id="langCode">FR</span>', '<span id="langCode">%s</span>' % lang.upper(), page)
    page = sub1(r'(?<=<button class="lang-btn" id="langBtn" aria-haspopup="true" aria-expanded="false">\n          <span class="flag">)<svg viewBox="0 0 24 16"><use href="#flag-fr-src"/></svg>',
                '<svg viewBox="%s"><use href="%s"/></svg>' % FLAG[lang], page)
    page = sub1(r'<div class="lang-opt" data-lang="%s"' % lang, '<div class="lang-opt active" data-lang="%s"' % lang, page)
    page = page.replace('href="/mentions-legales"', 'href="%s"' % LEGAL[lang])
    page = sub1(r"<script>\nconst I18N = ", '<script>window.SGCI_LANG="%s";</script>\n<script>\nconst I18N = ' % lang, page)

    # head
    url = BASE + HOME[lang]
    page = sub1(r"<title>.*?</title>", "<title>%s</title>" % esc(TITLE[lang]), page)
    page = sub1(r'(?<=<meta name="description" id="meta-desc" content=")[^"]*', att(d["_meta"]), page)
    page = sub1(r'<meta property="og:title" content="[^"]*" />', '<meta property="og:title" content="%s" />' % att(OGT[lang]), page)
    page = sub1(r'<meta property="og:description" content="[^"]*" />', '<meta property="og:description" content="%s" />' % att(d["_meta"]), page)
    page = sub1(r'<meta property="og:url" content="[^"]*" />',
                '<meta property="og:url" content="%s" />\n<meta property="og:locale" content="%s" />\n<meta property="og:site_name" content="SGCI SARLU" />\n'
                '<meta property="og:image" content="%s/og-image.png" />\n<meta property="og:image:width" content="1200" />\n<meta property="og:image:height" content="630" />\n'
                '<meta name="twitter:card" content="summary_large_image" />\n<meta name="twitter:image" content="%s/og-image.png" />\n<link rel="icon" href="%s" />'
                % (url, LOCALE[lang], BASE, BASE, FAVICON), page)
    page = sub1(r'<link rel="canonical" href="[^"]*" />\n(<link rel="alternate" hreflang="\w+" href="[^"]*" />\n){3}',
                '<link rel="canonical" href="%s" />\n' % url
                + "".join('<link rel="alternate" hreflang="%s" href="%s%s" />\n' % (l, BASE, HOME[l]) for l in ("fr", "en", "ar"))
                + '<link rel="alternate" hreflang="x-default" href="%s/" />\n<script type="application/ld+json">%s</script>\n' % (BASE, ld(ORG)), page)
    page = page.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n<!-- Generated by scripts/build_site.py from src/index.html — do not edit this file. -->", 1)
    out = ROOT / OUT[lang]
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print("%-16s %6d bytes" % (OUT[lang], len(page.encode("utf-8"))))


# ---------- inner pages (articles, legal notice, 404) ----------
UI = {"fr": {"home": "Accueil", "back": "← Retour au site", "news": "Actualités", "photos": "En images", "all": "Toutes les actualités",
             "sub": "Or · Niger", "copy": "© 2026 Société Générale de Commerce et de l'Industrie SARLU — Tous droits réservés.", "legal": "Mentions légales",
             "skip": "Aller au contenu", "contact": "Contact"},
      "en": {"home": "Home", "back": "← Back to the site", "news": "News", "photos": "In pictures", "all": "All news",
             "sub": "Gold · Niger", "copy": "© 2026 Société Générale de Commerce et de l'Industrie SARLU — All rights reserved.", "legal": "Legal notice",
             "skip": "Skip to content", "contact": "Contact"}}


def shell(lang, title, desc, canonical, body, alternates="", other=None, image=None, robots="index, follow", extra_head=""):
    u = UI[lang]
    lg = '<a class="lg" href="%s" hreflang="%s">%s</a>' % (other[1], other[0], other[0].upper()) if other else ""
    return ('<!DOCTYPE html>\n<!-- Generated by scripts/build_site.py — do not edit this file. -->\n<html lang="%s" dir="ltr">\n<head>\n<meta charset="UTF-8" />\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n<title>%s</title>\n<meta name="description" content="%s" />\n'
            '<meta name="robots" content="%s" />\n<meta name="theme-color" content="#0B2545" />\n<link rel="canonical" href="%s" />\n%s'
            '<meta property="og:type" content="article" />\n<meta property="og:site_name" content="SGCI SARLU" />\n<meta property="og:title" content="%s" />\n'
            '<meta property="og:description" content="%s" />\n<meta property="og:url" content="%s" />\n<meta property="og:image" content="%s" />\n'
            '<meta name="twitter:card" content="summary_large_image" />\n<link rel="icon" href="%s" />\n%s\n<link rel="stylesheet" href="/assets/pages.css" />\n%s</head>\n<body>\n'
            '<a class="skip" href="#main">%s</a>\n<header class="p-head"><div class="wrap">\n'
            '  <a href="%s" class="brand"><div class="brand-mark">S</div><div class="brand-txt"><b>SGCI</b><span>%s</span></div></a>\n'
            '  <nav class="p-nav" aria-label="%s"><a class="hide-s" href="%s#news">%s</a><a class="hide-s" href="%s#contact">%s</a><a href="%s">%s</a>%s</nav>\n'
            '</div></header>\n<main id="main">\n%s\n</main>\n<footer><div class="wrap foot"><div class="foot-copy">%s</div><a href="%s">%s</a></div></footer>\n</body>\n</html>\n'
            % (lang, esc(title), att(desc), robots, canonical, alternates, att(title), att(desc), canonical, image or BASE + "/og-image.png", FAVICON, FONTS, extra_head,
               u["skip"], HOME[lang], u["sub"], u["news"], HOME[lang], u["news"], HOME[lang], u["contact"], HOME[lang], u["back"], lg,
               body, u["copy"], LEGAL[lang], u["legal"]))


def build_articles(arts):
    urls = []
    for a in arts:
        langs = [l for l in ("fr", "en") if l in a]
        alt = "".join('<link rel="alternate" hreflang="%s" href="%s%s" />\n' % (l, BASE, art_url(a, l)) for l in langs) if len(langs) > 1 else ""
        for l in langs:
            t, u = a[l], UI[l]
            url = BASE + art_url(a, l)
            parts = ['<h2>%s</h2>' % esc(b["h"]) if "h" in b else '<p>%s</p>' % esc(b["p"]) for b in t["body"]]
            date = fmt_date(a.get("date"), l)
            figs = "".join('<figure><img src="%s" alt="%s" loading="lazy" decoding="async" /><figcaption>%s</figcaption></figure>\n'
                           % (p["file"], att(p.get(l, "")), esc(p.get(l, ""))) for p in a.get("photos", []))
            body = ('<section class="p-hero"><div class="wrap">\n  <div class="p-eyebrow">%s</div>\n  <h1>%s</h1>\n  <p class="p-lead">%s</p>\n%s</div></section>\n'
                    '<div class="wrap p-cover"><img src="%s" alt="%s" width="1020" height="765" /></div>\n'
                    '<article class="wrap"><div class="p-body">\n%s\n<p class="p-sign">SGCI SARLU · <a href="mailto:contact@sgci-niger.com">contact@sgci-niger.com</a> · +227 90 50 53 50</p>\n</div></article>\n'
                    % (esc(t.get("category", u["news"])), esc(t["title"]), esc(t["lead"]),
                       ('  <div class="p-date">%s</div>\n' % date) if date else "", a["cover"], att(t.get("cover_alt", "")), "\n".join(parts)))
            if figs:
                body += '<section class="p-gallery"><div class="wrap">\n<h2>%s</h2>\n<div class="p-grid">\n%s</div>\n</div></section>\n' % (u["photos"], figs)
            body += '<div class="wrap p-back"><a class="btn" href="%s#news">%s</a></div>' % (HOME[l], u["all"])
            news_ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": t["title"], "inLanguage": l,
                       "image": [BASE + a["cover"]], "publisher": {"@type": "Organization", "name": "SGCI SARLU", "url": BASE}}
            if a.get("date"):
                news_ld["datePublished"] = a["date"]
            other = [(o, art_url(a, o)) for o in langs if o != l]
            page = shell(l, t["title"] + " — SGCI", t["lead"][:155], url, body, alt, other[0] if other else None, BASE + a["cover"],
                         "index, follow" if a.get("status") == "published" else "noindex",
                         '<script type="application/ld+json">%s</script>\n' % ld(news_ld))
            out = ROOT / (art_url(a, l).lstrip("/") + ".html")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page, encoding="utf-8")
            print(out.relative_to(ROOT))
            if a.get("status") == "published":
                urls.append(art_url(a, l))
    return urls


LEGAL_TXT = {
 "fr": ("Mentions légales", "Informations légales sur l'éditeur du site sgci-niger.com.", "mentions-legales.html", """
<h2>Éditeur du site</h2>
<table>
<tr><td>Dénomination</td><td>Société Générale de Commerce et de l'Industrie — SGCI SARLU</td></tr>
<tr><td>Forme</td><td>Société à responsabilité limitée unipersonnelle de droit nigérien (OHADA)</td></tr>
<tr><td>Siège</td><td>Agadez, République du Niger</td></tr>
<tr><td>RCCM</td><td>NE-NIM-2024-B13-0346</td></tr>
<tr><td>NIF</td><td>123872/R</td></tr>
<tr><td>Activité</td><td>Exploitation et valorisation de l'or — site d'AMZEGUER, Tabelot, région d'Agadez</td></tr>
<tr><td>Contact</td><td><a href="mailto:contact@sgci-niger.com">contact@sgci-niger.com</a> · +227 90 50 53 50</td></tr>
<tr><td>Publication</td><td>La Direction Générale de SGCI SARLU</td></tr>
</table>
<h2>Hébergement</h2>
<p>Le site est hébergé par Vercel Inc., 440 N Barranca Avenue #4133, Covina, CA 91723, États-Unis — vercel.com.</p>
<h2>Propriété intellectuelle</h2>
<p>Les textes, photographies, logos et éléments graphiques de ce site sont la propriété de SGCI SARLU ou sont utilisés avec l'accord de leurs auteurs. Toute reproduction, totale ou partielle, est soumise à l'autorisation écrite préalable de SGCI.</p>
<h2>Informations publiées</h2>
<p>Les informations de ce site sont fournies à titre de présentation générale de la société et de ses activités. Elles ne constituent ni une offre de titres, ni une sollicitation d'investissement. Seuls les documents contractuels remis par SGCI font foi.</p>
<h2>Données personnelles</h2>
<p>Ce site n'utilise aucun cookie publicitaire ni outil de suivi. Les adresses e-mail transmises pour une demande de dossier ou une inscription aux alertes servent uniquement à répondre à cette demande et à envoyer les avis d'opportunités de SGCI ; elles ne sont pas cédées à des tiers. Vous pouvez demander l'accès à vos données, leur rectification ou leur suppression en écrivant à <a href="mailto:contact@sgci-niger.com">contact@sgci-niger.com</a>.</p>
"""),
 "en": ("Legal notice", "Legal information about the publisher of sgci-niger.com.", "en/legal-notice.html", """
<h2>Publisher</h2>
<table>
<tr><td>Company name</td><td>Société Générale de Commerce et de l'Industrie — SGCI SARLU</td></tr>
<tr><td>Legal form</td><td>Single-member limited liability company under Nigerien law (OHADA)</td></tr>
<tr><td>Head office</td><td>Agadez, Republic of Niger</td></tr>
<tr><td>Trade register (RCCM)</td><td>NE-NIM-2024-B13-0346</td></tr>
<tr><td>Tax number (NIF)</td><td>123872/R</td></tr>
<tr><td>Business</td><td>Gold mining and processing — AMZEGUER site, Tabelot, Agadez region</td></tr>
<tr><td>Contact</td><td><a href="mailto:contact@sgci-niger.com">contact@sgci-niger.com</a> · +227 90 50 53 50</td></tr>
<tr><td>Publication</td><td>The General Management of SGCI SARLU</td></tr>
</table>
<h2>Hosting</h2>
<p>This website is hosted by Vercel Inc., 440 N Barranca Avenue #4133, Covina, CA 91723, United States — vercel.com.</p>
<h2>Intellectual property</h2>
<p>The texts, photographs, logos and graphic elements of this website belong to SGCI SARLU or are used with their authors' consent. Any reproduction, in whole or in part, requires SGCI's prior written authorisation.</p>
<h2>Published information</h2>
<p>The information on this website is a general presentation of the company and its activities. It is neither an offer of securities nor a solicitation to invest. Only the contractual documents issued by SGCI are binding.</p>
<h2>Personal data</h2>
<p>This website uses no advertising cookies and no tracking tools. E-mail addresses sent to request a file or to register for alerts are used only to answer that request and to send SGCI's opportunity notices; they are not passed on to third parties. You may request access to, correction of or deletion of your data by writing to <a href="mailto:contact@sgci-niger.com">contact@sgci-niger.com</a>.</p>
"""),
}


def build_static():
    alt = ('<link rel="alternate" hreflang="fr" href="%s/mentions-legales" />\n<link rel="alternate" hreflang="en" href="%s/en/legal-notice" />\n' % (BASE, BASE))
    for l, (title, desc, out, text) in LEGAL_TXT.items():
        body = ('<section class="p-hero"><div class="wrap">\n  <div class="p-eyebrow">SGCI SARLU</div>\n  <h1>%s</h1>\n</div></section>\n'
                '<article class="wrap"><div class="p-body">%s</div></article>' % (title, text))
        o = "en" if l == "fr" else "fr"
        page = shell(l, title + " — SGCI", desc, BASE + LEGAL[l], body, alt, (o, LEGAL[o]))
        (ROOT / out).parent.mkdir(exist_ok=True)
        (ROOT / out).write_text(page, encoding="utf-8")
        print(out)
    body = ('<section class="p-hero"><div class="wrap">\n  <div class="p-eyebrow">Erreur 404</div>\n  <h1>Page introuvable</h1>\n'
            '  <p class="p-lead">La page demandée n\'existe pas ou a été déplacée. · The page you are looking for does not exist or has moved.</p>\n</div></section>\n'
            '<div class="wrap p-back"><a class="btn" href="/">Retour à l\'accueil</a></div>')
    (ROOT / "404.html").write_text(shell("fr", "Page introuvable — SGCI", "Page introuvable.", BASE + "/404", body, robots="noindex"), encoding="utf-8")
    print("404.html")


def build_sitemap(article_urls):
    rows = ['  <url><loc>%s%s</loc><priority>%s</priority></url>' % (BASE, p, pr) for p, pr in
            [("/", "1.0"), ("/en", "0.9"), ("/ar", "0.9")] + [(u, "0.7") for u in article_urls] + [("/mentions-legales", "0.3"), ("/en/legal-notice", "0.3")]]
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(rows), encoding="utf-8")
    print("sitemap.xml  (%d urls)" % len(rows))


if __name__ == "__main__":
    src = (ROOT / "src" / "index.html").read_text(encoding="utf-8")
    i18n, arts = load_i18n(src), load_articles()
    for lang in ("fr", "en", "ar"):
        build_home(src, i18n, arts, lang)
    urls = build_articles(arts)
    build_static()
    build_sitemap(urls)
    print("articles shown: %d%s" % (len(arts), "  (drafts included)" if DRAFTS else ""))
