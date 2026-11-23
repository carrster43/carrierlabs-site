#!/usr/bin/env python3
"""
Build the app pages on carrierlabs.org from the carrierpress.com site repo.

    python3 make_apps.py

WHAT IT WRITES
  apps/index.html        the icon grid (only the part between the apps:grid markers)
  apps/<slug>/index.html one short detail page per app: icon, what it does, price,
                         one button, the screenshots, then a link to the full page
  apps/icons/<slug>.webp copied from carrierpress-site/apps/icons/
  index.html             the app row at the top of the homepage (apps:row markers)
  sitemap.xml            every page above

WHY A DETAIL PAGE HERE (author 2026-11-23). A tap on an icon used to land on the
app's full carrierpress.com page, about seven phone screens long, and "you kind of
get lost". The detail page is the card alone, App Store style; the full page is one
link away for anyone who wants everything.

WHERE THE FACTS COME FROM, so a price is never typed twice:
  carrierpress-site/apps/index.html        the card: name, blurb, price, note, links
  carrierpress-site/apps/<slug>/index.html the hero: status line, main button, price
  carrierpress-site/apps/shots/<slug>/     the screenshots, alts.json, captions.json
  carrierpress-site/apps/icons/            icons and accents.json
Rerun after any change to an app on carrierpress.com, then commit and push.

LEFT OFF ON PURPOSE: apps folded into another app (folds.FOLDED, plus Permit Path,
which lives inside Who Serves). Customers never see a folded app's old name.
"""
import html, json, os, pathlib, re, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
PRESS = pathlib.Path(os.environ.get("PRESS_SITE", pathlib.Path.home() / "Projects/carrierpress-site"))
PRESS_URL = "https://carrierpress.com"
LABS_URL = "https://carrierlabs.org"
FOLDED_EXTRA = {"permitpath"}  # Who Serves carries the permit checklists now (author 2026-11-22)


def folded():
    sys.path.insert(0, str(PRESS))
    try:
        import folds
        return set(folds.FOLDED) | FOLDED_EXTRA
    finally:
        sys.path.pop(0)


def absolute(href, slug):
    if href.startswith("#"):
        return "%s/apps/%s/%s" % (PRESS_URL, slug, href)
    if href.startswith("/"):
        return PRESS_URL + href
    return href


def text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def first(pattern, s, default=""):
    m = re.search(pattern, s, re.S)
    return m.group(1).strip() if m else default


def read_apps():
    skip = folded()
    cards = (PRESS / "apps/index.html").read_text()
    alts = json.loads((PRESS / "apps/shots/alts.json").read_text())
    caps = json.loads((PRESS / "apps/shots/captions.json").read_text())
    accents = json.loads((PRESS / "apps/icons/accents.json").read_text())
    apps = []
    for cls, body in re.findall(r'<article class="(ap-card[^"]*)">(.*?)</article>', cards, re.S):
        slug = first(r'href="/apps/([a-z0-9]+)/"', body)
        if not slug or slug in skip:
            continue
        badge = text(first(r'class="ap-badge">(.*?)</span>\s*</div>', body))
        is_open = "is-open" in cls
        if not is_open and badge != "Coming soon":
            continue
        page = (PRESS / "apps" / slug / "index.html").read_text()
        btn = None
        for href, inner in re.findall(r'<a class="lp-btn[^"]*" href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
            if href != "/support/":  # the tip ask is not the app's own next step
                btn = (absolute(href, slug), first(r"^(.*?)<small>", inner) or inner,
                       first(r"<small>(.*?)</small>", inner))
                break
        links = [(absolute(h, slug), t) for h, t in
                 re.findall(r'<a href="([^"]+)">(.*?)</a>', first(r'<div class="ap-links">(.*?)</div>', body))
                 if "waitlist" not in h]
        shots = []
        folder = PRESS / "apps/shots" / slug
        for sm in sorted(folder.glob("*-sm.webp")) if folder.is_dir() else []:
            name = sm.name[:-len("-sm.webp")]
            key = "%s/%s" % (slug, name)
            shots.append(dict(sm="%s/apps/shots/%s/%s" % (PRESS_URL, slug, sm.name),
                              full="%s/apps/shots/%s/%s.webp" % (PRESS_URL, slug, name),
                              alt=alts.get(key, ""), caption=caps.get(key, ""), web=name.startswith("web-")))
        if any(s["web"] for s in shots):
            shots = [s for s in shots if s["web"]]  # web captures win, as on carrierpress.com
        price_html = first(r'<p class="lp-price">(.*?)</p>', page)
        apps.append(dict(
            slug=slug, name=text(first(r"<h3>(.*?)</h3>", body)), soon=not is_open,
            status=text(first(r'<span class="lp-status">(.*?)</span>', page)) or badge,
            blurb=first(r'<p class="ap-blurb">(.*?)</p>', body),
            note=first(r'<p class="ap-note">(.*?)</p>', body),
            tag=first(r'<span class="tag">(.*?)</span>', body),
            price=first(r"^(.*?)<span>", price_html) or price_html,
            renew=first(r"<span>(.*?)</span>", price_html),
            button=btn, links=links, shots=shots,
            accent=accents.get(slug, "#151a33")))
    apps.sort(key=lambda a: a["name"].lower())
    return apps


def head(title, desc, canonical, css_up):
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            "<title>%s</title><meta name=\"description\" content=\"%s\">\n"
            "<link rel=\"canonical\" href=\"%s\"><meta property=\"og:title\" content=\"%s\">"
            "<meta property=\"og:description\" content=\"%s\"><meta property=\"og:type\" content=\"website\">"
            "<meta name=\"twitter:card\" content=\"summary\">\n"
            "<link rel=\"icon\" href=\"%sfavicon.png\" type=\"image/png\"><link rel=\"stylesheet\" href=\"%sstyles.css\">"
            "<link rel=\"stylesheet\" href=\"%sapps/apps.css\">\n</head>\n"
            % (html.escape(title), html.escape(desc), canonical, html.escape(title), html.escape(desc),
               css_up, css_up, css_up))


FOOT = ('<footer class="wrap">&copy; 2026 Carrier Labs LLC, Diamondhead, Mississippi. Part of '
        '<a href="https://carrierventures.org/">Carrier Ventures</a> &middot; '
        '<a href="https://carrierpress.com/">Carrier Press</a></footer>')


def ext(href):
    return ' target="_blank" rel="noopener"' if not href.startswith(PRESS_URL) else ""


def detail(app, prev, nxt):
    s, n = app["slug"], html.escape(app["name"])
    full = "%s/apps/%s/" % (PRESS_URL, s)
    b = [head("%s, from Carrier Labs" % app["name"], text(app["blurb"]), full, "../../")]
    b.append('<body class="dt">\n<div class="dt-band" style="--accent:%s"><div class="wrap">\n' % app["accent"])
    b.append('<nav class="dt-nav"><a href="../">&lsaquo; All apps</a></nav>\n')
    b.append('<div class="dt-id"><img class="dt-icon" src="../icons/%s.webp" alt="" width="96" height="96">'
             '<div><h1>%s</h1><span class="dt-status">%s</span></div></div>\n'
             % (s, n, html.escape(app["status"])))
    b.append('<p class="dt-blurb">%s</p>\n' % app["blurb"])
    if app["button"]:
        href, label, small = app["button"]
        b.append('<div class="dt-buy"><a class="dt-btn" href="%s"%s>%s<small>%s</small></a>'
                 % (html.escape(href), ext(href), label, small))
    else:
        b.append('<div class="dt-buy"><a class="dt-btn" href="%s">See %s<small>Prices, a sample and more</small></a>'
                 % (full, n))
    if app["price"]:
        b.append('<p class="dt-price">%s%s</p>' % (app["price"], "<span>%s</span>" % app["renew"] if app["renew"] else ""))
    b.append("</div>\n</div></div>\n<main class=\"wrap dt-main\">\n")
    if app["shots"]:
        b.append('<h2 class="dt-h">Screens</h2>\n<div class="dt-shots" tabindex="0" role="region" '
                 'aria-label="%s screens, scroll sideways">' % n)
        for sh in app["shots"]:
            cap = '<figcaption>%s</figcaption>' % html.escape(sh["caption"]) if sh["caption"] else ""
            b.append('<figure><a href="%s"><img src="%s" alt="%s" width="180" height="390" loading="lazy" '
                     'decoding="async"></a>%s</figure>' % (sh["full"], sh["sm"], html.escape(sh["alt"]), cap))
        b.append("</div>\n")
        if all(sh["web"] for sh in app["shots"]):
            b.append('<p class="dt-fine">Screens show the web version with demonstration data.</p>\n')
    if app["note"]:
        b.append('<h2 class="dt-h">What it does</h2>\n<p class="dt-note">%s</p>\n' % app["note"])
    if app["tag"]:
        b.append('<p class="dt-tag">%s</p>\n' % app["tag"])
    more = ['<a class="dt-all" href="%s">Everything about %s &rsaquo;</a>' % (full, n)]
    more += ['<a href="%s">%s</a>' % (html.escape(h), t) for h, t in app["links"] if h.rstrip("/") != full.rstrip("/")]
    b.append('<p class="dt-more">%s</p>\n' % " ".join(more))
    b.append('<nav class="dt-step" aria-label="More apps"><a href="../%s/">&lsaquo; %s</a>'
             '<a href="../">All apps</a><a href="../%s/">%s &rsaquo;</a></nav>\n'
             % (prev["slug"], html.escape(prev["name"]), nxt["slug"], html.escape(nxt["name"])))
    b.append("</main>\n%s\n</body></html>\n" % FOOT)
    return "".join(b)


def tile(app, prefix, i=None):
    soon = '<span class="soon">Soon</span>' if app["soon"] else ""
    li = ' style="--i:%d"' % i if i is not None else ""
    return ('<li%s><a class="app" href="%s%s/" data-accent="%s"><span class="tile">'
            '<img src="%sicons/%s.webp" alt="" width="84" height="84">%s</span>'
            '<span class="name">%s</span></a></li>'
            % (li, prefix, app["slug"], app["accent"], prefix, app["slug"], soon, html.escape(app["name"])))


def splice(path, tag, inner):
    s = path.read_text()
    start, end = "<!-- %s:start -->" % tag, "<!-- %s:end -->" % tag
    if s.count(start) != 1 or s.count(end) != 1:
        sys.exit("%s: expected one %s and one %s" % (path, start, end))
    a, rest = s.split(start)
    _, b = rest.split(end)
    path.write_text(a + start + "\n" + inner + "\n" + end + b)


def main():
    apps = read_apps()
    icons = HERE / "apps/icons"
    icons.mkdir(parents=True, exist_ok=True)
    for a in apps:
        src = PRESS / "apps/icons" / ("%s.webp" % a["slug"])
        if not src.exists():
            sys.exit("no icon for %s at %s" % (a["slug"], src))
        shutil.copy2(src, icons / src.name)
    for i, a in enumerate(apps):
        out = HERE / "apps" / a["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(detail(a, apps[i - 1], apps[(i + 1) % len(apps)]))
    splice(HERE / "apps/index.html", "apps:grid",
           "<ul class=\"springboard\">\n%s\n</ul>" % "\n".join(tile(a, "", i) for i, a in enumerate(apps)))
    splice(HERE / "index.html", "apps:row",
           '<section class="approw" aria-labelledby="approw-h"><div class="approw-top">'
           '<h2 id="approw-h">Apps from Carrier Labs</h2><a href="apps/">See all %d</a></div>'
           '<ul class="approw-list">%s</ul></section>'
           % (len(apps), "".join(tile(a, "apps/") for a in apps)))
    urls = ["", "apps/"] + ["apps/%s/" % a["slug"] for a in apps]
    (HERE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n'
        % "\n".join("  <url><loc>%s/%s</loc></url>" % (LABS_URL, u) for u in urls))
    print("%d apps: grid, %d detail pages, homepage row, sitemap %d urls"
          % (len(apps), len(apps), len(urls)))
    for a in apps:
        if not a["shots"]:
            print("  no screenshots yet: %s" % a["name"])


if __name__ == "__main__":
    main()
