#!/usr/bin/env python3
"""
Programmatic SEO page generator for cryptodcacalculator.com

Generates static "If you invested $X in <coin> in <year>" landing pages that each
target a specific long-tail search query, using REAL Binance historical prices.

Run:  python3 generate_pages.py
Output: /if-you-invested/<amount>-in-<coin>-in-<year>/index.html  (+ a hub page)
        and appends the new URLs to sitemap.xml

No external dependencies (urllib only). Output is plain static HTML — no build
step at serve time, deploys to Cloudflare Pages as-is.
"""

import json
import os
import urllib.request
from datetime import datetime, timezone

SITE = "https://cryptodcacalculator.com"
ROOT = os.path.dirname(os.path.abspath(__file__))
NOW_MS = int(datetime(2026, 6, 17, tzinfo=timezone.utc).timestamp() * 1000)

# ── Coins (extend this list to expand coverage) ──────────────────────────────
COINS = {
    "bitcoin": {"symbol": "BTCUSDT", "name": "Bitcoin", "ticker": "BTC", "from_year": 2017},
    "ethereum": {"symbol": "ETHUSDT", "name": "Ethereum", "ticker": "ETH", "from_year": 2017},
    "solana":   {"symbol": "SOLUSDT", "name": "Solana",   "ticker": "SOL", "from_year": 2021},
    "bnb":      {"symbol": "BNBUSDT", "name": "BNB",       "ticker": "BNB", "from_year": 2018},
}

AMOUNTS = [100, 500, 1000, 5000]

# Per-year market narrative — keeps every page's prose genuinely unique (SEO).
YEAR_CONTEXT = {
    "bitcoin": {
        2017: "Bitcoin's breakout year. BTC exploded from around $1,000 in January to nearly $20,000 by mid-December, drawing mainstream attention for the first time before a sharp pullback.",
        2018: "The crypto winter. After the 2017 mania, Bitcoin spent the entire year grinding down — from ~$14,000 to roughly $3,200 by December. Buying here meant catching a falling knife, but at historically cheap prices.",
        2019: "A recovery and consolidation year. BTC climbed from ~$3,700 to a mid-year high near $13,000, then drifted back to settle around $7,000 — a calmer year between two storms.",
        2020: "The year everything changed. Bitcoin crashed to ~$3,800 in the March COVID panic, then began one of the most powerful bull runs in its history, ending the year near $29,000 as institutions started buying.",
        2021: "Peak euphoria. Bitcoin set two all-time highs — about $64,000 in April and nearly $69,000 in November — while surviving the China mining-ban crash mid-year. A volatile but historic year.",
        2022: "The reckoning. The Terra/Luna implosion and the FTX collapse dragged Bitcoin from ~$47,000 down to about $16,500 — one of the deepest bear markets crypto has seen.",
        2023: "Quiet accumulation. Recovering from the FTX lows, Bitcoin more than doubled over the year, climbing from ~$16,500 to around $42,000 as confidence slowly returned.",
        2024: "The institutional era. Spot Bitcoin ETFs were approved in January and the fourth halving arrived in April, pushing BTC past its previous all-time high and into six figures.",
    },
    "ethereum": {
        2017: "The ICO boom. Ethereum powered a wave of token sales, rising from under $10 early in the year to over $700 by December as developers flocked to build on it.",
        2018: "The crypto winter hit Ethereum hard. After peaking near $1,400 in January, ETH collapsed to around $85 by year end as the ICO bubble burst.",
        2019: "A rebuilding year. ETH ranged between roughly $85 and $350, ending around $130 while the foundations for DeFi were quietly being laid.",
        2020: "DeFi summer. Ethereum became the backbone of decentralized finance, climbing from ~$130 to around $740 as lending, swapping, and yield farming exploded.",
        2021: "Peak Ethereum. Driven by the NFT and DeFi mania, ETH set an all-time high near $4,800, and the EIP-1559 upgrade began burning fees.",
        2022: "Bear market and the Merge. Ethereum transitioned to proof-of-stake in September, but the broader downturn pulled ETH from ~$3,700 down to about $1,200.",
        2023: "Recovery and staking growth. ETH spent the year ranging roughly $1,200 to $2,400 as staking withdrawals went live and activity returned.",
        2024: "A new chapter. Spot Ethereum ETFs were approved and the Dencun upgrade slashed layer-2 costs, lifting ETH to new multi-year highs.",
    },
    "solana": {
        2021: "Solana's breakout. SOL exploded from under $2 to an all-time high near $260, earning the 'Ethereum killer' label as its fast, cheap network drew an NFT and DeFi boom.",
        2022: "The hardest fall. Closely tied to FTX and Alameda, Solana was hammered by the FTX collapse — SOL plunged from ~$170 to around $10, with many writing it off entirely.",
        2023: "The great comeback. Defying the doubters, SOL surged from ~$10 to over $100 as its ecosystem rebuilt and activity returned in force.",
        2024: "Sustained momentum. Solana rode a wave of memecoin and DeFi activity to new highs, cementing its place as a top smart-contract platform.",
    },
    "bnb": {
        2018: "BNB's first full year. Despite the broader bear market, Binance's exchange token held up better than most, trading roughly between $6 and $15.",
        2019: "Growing with Binance. As the exchange expanded, BNB climbed from around $6 to over $30, powered by token burns and exchange utility.",
        2020: "Steady then surging. BNB spent much of the year around $15 before joining the late-year rally, ending near $37 ahead of a massive run.",
        2021: "The BSC boom. With the rise of Binance Smart Chain, BNB exploded to an all-time high near $690 as users sought a cheaper alternative to Ethereum.",
        2022: "Resilient in the downturn. BNB fell from ~$530 to about $240 during the bear market, but held up better than most large-cap coins.",
        2023: "Under pressure. Amid regulatory scrutiny of Binance, BNB ranged roughly between $240 and $330 for most of the year.",
        2024: "Market recovery. BNB rose with the broader crypto rebound as Binance Smart Chain activity picked back up.",
    },
}

BINANCE = "https://data-api.binance.vision/api/v3/klines"


def fetch_history(symbol):
    """Full daily close history: list of [openTimeMs, close]."""
    prices, cursor, guard = [], 0, 0
    while guard < 40:
        guard += 1
        url = f"{BINANCE}?symbol={symbol}&interval=1d&startTime={cursor}&endTime={NOW_MS}&limit=1000"
        with urllib.request.urlopen(url) as r:
            rows = json.load(r)
        if not rows:
            break
        for row in rows:
            prices.append([row[0], float(row[4])])
        if len(rows) < 1000:
            break
        cursor = rows[-1][0] + 86_400_000
    return prices


def price_at(prices, ts):
    """Nearest close at or before ts (binary search)."""
    lo, hi, best = 0, len(prices) - 1, prices[0]
    while lo <= hi:
        mid = (lo + hi) // 2
        if prices[mid][0] <= ts:
            best = prices[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best[1]


def first_on_or_after(prices, ts):
    """First [ts, price] at or after ts."""
    for p in prices:
        if p[0] >= ts:
            return p
    return prices[-1]


def fmt_usd(n):
    return "$" + format(int(round(n)), ",")


def fmt_mult(x):
    return f"{x:.1f}x" if x < 10 else f"{round(x)}x"


def compute(prices, year, amount):
    """Lump sum invested at the start of `year`, plus a weekly-DCA comparison."""
    jan1 = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    entry = first_on_or_after(prices, jan1)
    entry_ts, entry_price = entry[0], entry[1]
    now_price = prices[-1][1]

    # Lump sum
    coins = amount / entry_price
    lump_value = coins * now_price
    roi = (lump_value - amount) / amount * 100
    mult = lump_value / amount

    # Weekly DCA over the same window, same total capital
    week = 7 * 86_400_000
    buys = list(range(entry_ts, NOW_MS + 1, week))
    per_buy = amount / len(buys)
    dca_coins = sum(per_buy / price_at(prices, t) for t in buys)
    dca_value = dca_coins * now_price

    return {
        "entry_date": datetime.utcfromtimestamp(entry_ts / 1000).strftime("%B %-d, %Y")
        if os.name != "nt" else datetime.utcfromtimestamp(entry_ts / 1000).strftime("%B %d, %Y"),
        "entry_price": entry_price,
        "now_price": now_price,
        "coins": coins,
        "lump_value": lump_value,
        "roi": roi,
        "mult": mult,
        "dca_value": dca_value,
    }


def slug(amount, coin, year):
    return f"{amount}-in-{coin}-in-{year}"


CSS = """
  :root{--bg:#07101f;--card:#0d1b2e;--text:#e8edf5;--muted:#5f7298;--accent:#3b82f6;--green:#22c55e;--red:#ef4444;--line:rgba(255,255,255,.09);--sans:system-ui,-apple-system,sans-serif}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:var(--sans);line-height:1.6}
  a{color:var(--accent);text-decoration:none}
  .header{text-align:center;padding:48px 20px 28px;border-bottom:1px solid var(--line)}
  .header a.back{font-size:13px;color:var(--muted);display:block;margin-bottom:16px}
  .header a.back:hover{color:var(--accent)}
  h1{font-size:clamp(23px,4vw,36px);font-weight:700;letter-spacing:-.5px;margin-bottom:10px;max-width:760px;margin-left:auto;margin-right:auto}
  .sub{font-size:15px;color:var(--muted);max-width:560px;margin:0 auto}
  .hero{max-width:680px;margin:32px auto 0;padding:0 20px}
  .hero-card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px 24px;text-align:center}
  .hero-card .big{font-size:clamp(40px,9vw,64px);font-weight:800;letter-spacing:-1.5px;line-height:1}
  .hero-card .big.pos{color:var(--green)}.hero-card .big.neg{color:var(--red)}
  .hero-card .big-sub{font-size:14px;color:var(--muted);margin-top:8px}
  .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:22px}
  .grid .cell{background:rgba(255,255,255,.03);border-radius:12px;padding:12px 8px}
  .grid .k{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
  .grid .v{font-size:17px;font-weight:700;margin-top:3px}
  .v.pos{color:var(--green)}
  .cta-box{max-width:680px;margin:22px auto;padding:0 20px}
  .cta-btn{display:block;width:100%;padding:17px;background:var(--accent);color:#fff;font-weight:700;font-size:16px;text-align:center;border-radius:14px;transition:.15s}
  .cta-btn:hover{background:#2563eb}
  .cta-btn small{display:block;font-weight:400;font-size:12px;opacity:.85;margin-top:3px}
  .aff{display:block;max-width:640px;margin:10px auto;padding:0 20px}
  .aff a{display:block;padding:14px;border-radius:13px;text-align:center;font-weight:600;font-size:14px;border:1px solid var(--line)}
  .aff a.binance{background:rgba(240,185,11,.08);border-color:rgba(240,185,11,.3);color:#f0b90b}
  .aff a.ledger{background:rgba(255,163,26,.07);border-color:rgba(255,163,26,.3);color:#ffa31a}
  .content{max-width:720px;margin:0 auto;padding:34px 20px 50px}
  .content h2{font-size:20px;font-weight:700;margin:2rem 0 .8rem}
  .content p{font-size:15px;color:#b0bdd4;margin-bottom:1rem;line-height:1.75}
  .related{max-width:720px;margin:0 auto;padding:0 20px 40px}
  .related h2{font-size:18px;font-weight:700;margin-bottom:14px}
  .chips{display:flex;flex-wrap:wrap;gap:8px}
  .chips a{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 13px;font-size:13px;color:var(--text)}
  .chips a:hover{border-color:var(--accent);color:var(--accent)}
  .faq{border-top:1px solid var(--line);padding-top:2rem;margin-top:1rem}
  .faq h2{font-size:21px;font-weight:700;margin-bottom:1.3rem}
  .faq-item{border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:12px;background:var(--card)}
  .faq-item h3{font-size:15px;font-weight:600;margin-bottom:.5rem}
  .faq-item p{font-size:14px;color:var(--muted);margin:0}
  .disclaimer{font-size:12px;color:var(--muted);text-align:center;padding:20px;border-top:1px solid var(--line)}
"""

GA = ('<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q37F2112N1"></script>'
      '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
      "gtag('js',new Date());gtag('config','G-Q37F2112N1');</script>")

ADSENSE = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
           '?client=ca-pub-8050477522540695" crossorigin="anonymous"></script>')

BINANCE_REF = "https://www.binance.com/register?ref=392703655&utm_medium=web_share_copy"
LEDGER_REF = "https://shop.ledger.com/?r=ac732785d3ea"


def page_html(coin, cfg, year, amount, d, siblings):
    name, ticker = cfg["name"], cfg["ticker"]
    val = fmt_usd(d["lump_value"])
    roi_txt = ("+" if d["roi"] >= 0 else "") + f"{d['roi']:.0f}%"
    cls = "pos" if d["roi"] >= 0 else "neg"
    title = f"If You Invested {fmt_usd(amount)} in {name} in {year} — What It's Worth in 2026"
    desc = (f"If you had invested {fmt_usd(amount)} in {name} ({ticker}) in {year}, "
            f"it would be worth {val} today — a {roi_txt} return ({fmt_mult(d['mult'])}). "
            f"See the real numbers and backtest your own.")
    url = f"{SITE}/if-you-invested/{slug(amount, coin, year)}/"
    calc_link = f"{SITE}/#{coin},weekly,100,{year}-01-01,2026-06-17"
    ctx = YEAR_CONTEXT.get(coin, {}).get(year, "")
    dca_val = fmt_usd(d["dca_value"])

    faq = [
        (f"How much would {fmt_usd(amount)} in {name} in {year} be worth today?",
         f"If you had invested {fmt_usd(amount)} in {name} at the start of {year} "
         f"(around {fmt_usd(d['entry_price'])} per {ticker}), it would be worth approximately "
         f"{val} today — a return of {roi_txt}, based on real Binance price data."),
        (f"Was {year} a good year to buy {name}?",
         ctx + f" A {fmt_usd(amount)} lump sum bought roughly {d['coins']:.4f} {ticker} at that time."),
        ("Would dollar-cost averaging have done better?",
         f"Spreading the same {fmt_usd(amount)} as weekly buys from {year} to today would be worth "
         f"about {dca_val}. Lump sum tends to win when you buy near a low; DCA reduces timing risk. "
         f"Use the calculator to compare both for any date."),
        (f"Where does this {name} price data come from?",
         "Real daily close prices from Binance public market data (data-api.binance.vision). "
         "Figures are gross of fees and taxes, for educational purposes only."),
    ]
    faq_json = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq],
    }
    breadcrumb_json = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "If You Invested",
             "item": SITE + "/if-you-invested/"},
            {"@type": "ListItem", "position": 3, "name": f"{fmt_usd(amount)} in {name} in {year}",
             "item": url},
        ],
    }

    chips = "".join(
        f'<a href="{SITE}/if-you-invested/{slug(a, c, y)}/">{fmt_usd(a)} in {n} in {y}</a>'
        for (a, c, y, n) in siblings)

    faq_html = "".join(
        f'<div class="faq-item"><h3>{q}</h3><p>{a}</p></div>' for q, a in faq)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/og-image.png" type="image/png">
{GA}
{ADSENSE}
<script type="application/ld+json">{json.dumps(faq_json)}</script>
<script type="application/ld+json">{json.dumps(breadcrumb_json)}</script>
<style>{CSS}</style>
</head>
<body>

<div class="header">
  <a href="{SITE}/if-you-invested/" class="back">&larr; All "what if I invested" scenarios</a>
  <h1>If you invested {fmt_usd(amount)} in {name} in {year}</h1>
  <p class="sub">Here's exactly what it would be worth today, based on real {ticker} prices from Binance.</p>
</div>

<div class="hero">
  <div class="hero-card">
    <div class="big {cls}">{val}</div>
    <div class="big-sub">value today from a {fmt_usd(amount)} investment in {year}</div>
    <div class="grid">
      <div class="cell"><div class="k">Invested</div><div class="v">{fmt_usd(amount)}</div></div>
      <div class="cell"><div class="k">Return</div><div class="v pos">{roi_txt}</div></div>
      <div class="cell"><div class="k">Multiple</div><div class="v">{fmt_mult(d['mult'])}</div></div>
      <div class="cell"><div class="k">{ticker} price then</div><div class="v">{fmt_usd(d['entry_price'])}</div></div>
      <div class="cell"><div class="k">{ticker} bought</div><div class="v">{d['coins']:.4f}</div></div>
      <div class="cell"><div class="k">{ticker} price now</div><div class="v">{fmt_usd(d['now_price'])}</div></div>
    </div>
  </div>
</div>

<div class="cta-box">
  <a class="cta-btn" href="{calc_link}">Backtest your own {name} investment &rarr;<small>Free &middot; Real Binance data &middot; No sign-up</small></a>
</div>
<div class="aff">
  <a class="binance" href="{BINANCE_REF}" target="_blank" rel="noopener">Ready to start? Open a free Binance account &rarr;</a>
</div>

<div class="content">
  <h2>What {fmt_usd(amount)} in {name} in {year} became</h2>
  <p>{ctx}</p>
  <p>If you had put {fmt_usd(amount)} into {name} at the start of {year} — buying around {fmt_usd(d['entry_price'])} per {ticker} on {d['entry_date']} — you would have acquired roughly {d['coins']:.4f} {ticker}. At today's price of {fmt_usd(d['now_price'])}, that position is worth about <strong>{val}</strong>, a return of {roi_txt} ({fmt_mult(d['mult'])} your money).</p>

  <h2>Lump sum vs dollar-cost averaging</h2>
  <p>The figure above assumes a single lump-sum buy at the start of {year}. If you had instead spread that same {fmt_usd(amount)} into equal weekly purchases from {year} until today, it would be worth about {dca_val}. Lump sum usually wins when you happen to buy near a market low, while dollar-cost averaging lowers your risk of buying right before a crash. There's no single right answer — it depends on the entry point and your risk tolerance.</p>

  <h2>Check any amount, coin, or date</h2>
  <p>These numbers are real, but they're just one scenario. Use the <a href="{calc_link}">free DCA calculator</a> to test any investment amount, any cryptocurrency, and any start date — with a live chart, ROI breakdown, and a side-by-side DCA vs lump-sum verdict.</p>
</div>

<div class="aff">
  <a class="ledger" href="{LEDGER_REF}" target="_blank" rel="noopener">Holding crypto long-term? Secure it on a Ledger wallet &rarr;</a>
</div>

<div class="related">
  <h2>Explore other scenarios</h2>
  <div class="chips">{chips}</div>
</div>

<div class="content" style="padding-top:0">
  <div class="faq">
    <h2>Frequently asked questions</h2>
    {faq_html}
  </div>
</div>

<p class="disclaimer">For educational purposes only. Figures use real Binance historical prices and exclude fees and taxes. Past performance does not guarantee future results. Not financial advice.</p>

</body>
</html>"""


def hub_html(all_pages):
    title = "If You Invested in Crypto — Real Historical Return Scenarios"
    desc = ("See exactly what your money would be worth if you'd invested in Bitcoin and other "
            "crypto in past years. Real Binance data, dozens of scenarios.")
    url = f"{SITE}/if-you-invested/"
    # group by coin then year
    groups = {}
    for (a, c, y, n, val, roi) in all_pages:
        groups.setdefault(n, []).append((a, c, y, n, val, roi))
    body = ""
    for name, items in groups.items():
        body += f"<h2>{name}</h2><div class='chips'>"
        for (a, c, y, n, val, roi) in sorted(items, key=lambda x: (x[2], x[0])):
            body += (f'<a href="{SITE}/if-you-invested/{slug(a, c, y)}/">'
                     f'{fmt_usd(a)} in {y} &rarr; {val}</a>')
        body += "</div>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<link rel="icon" href="/og-image.png" type="image/png">
{GA}
{ADSENSE}
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <a href="{SITE}/" class="back">&larr; Back to the DCA calculator</a>
  <h1>If you invested in crypto&hellip;</h1>
  <p class="sub">Real historical return scenarios, calculated from actual Binance prices. Pick one to see the full breakdown.</p>
</div>
<div class="related" style="padding-top:34px">{body}</div>
<p class="disclaimer">For educational purposes only. Real Binance historical prices, excluding fees and taxes. Not financial advice.</p>
</body>
</html>"""


def write(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def update_sitemap(urls):
    sm = os.path.join(ROOT, "sitemap.xml")
    today = "2026-06-17"
    entries = "".join(
        f"\n  <url><loc>{u}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>monthly</changefreq><priority>0.7</priority></url>"
        for u in urls)
    content = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">'
               if False else
               '<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    # Rebuild sitemap from the canonical set of URLs we know about.
    core = [SITE + "/", SITE + "/bitcoin-dca-calculator/", SITE + "/ethereum-dca-calculator/",
            SITE + "/solana-dca-calculator/", SITE + "/bnb-dca-calculator/",
            SITE + "/if-you-invested/"]
    core_entries = "".join(
        f"\n  <url><loc>{u}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>weekly</changefreq><priority>0.9</priority></url>" for u in core)
    core_entries += (f"\n  <url><loc>{SITE}/privacy-policy.html</loc><lastmod>{today}</lastmod>"
                     f"<changefreq>yearly</changefreq><priority>0.3</priority></url>")
    with open(sm, "w", encoding="utf-8") as f:
        f.write(content + core_entries + entries + "\n</urlset>\n")


def main():
    all_pages = []        # (amount, coin, year, name, value_str, roi)
    sitemap_urls = []
    histories = {}

    for coin, cfg in COINS.items():
        print(f"Fetching {cfg['symbol']} history...")
        histories[coin] = fetch_history(cfg["symbol"])
        years = list(range(cfg["from_year"], 2025))
        for year in years:
            for amount in AMOUNTS:
                d = compute(histories[coin], year, amount)
                all_pages.append((amount, coin, year, cfg["name"],
                                  fmt_usd(d["lump_value"]), d["roi"]))

    # second pass: write pages with sibling links
    for coin, cfg in COINS.items():
        years = list(range(cfg["from_year"], 2025))
        for year in years:
            for amount in AMOUNTS:
                d = compute(histories[coin], year, amount)
                # siblings = other amounts for same coin/year + same amount other years (capped)
                sibs = [(a, coin, year, cfg["name"]) for a in AMOUNTS if a != amount]
                sibs += [(amount, coin, y, cfg["name"]) for y in years if y != year]
                sibs = sibs[:10]
                html = page_html(coin, cfg, year, amount, d, sibs)
                out = os.path.join(ROOT, "if-you-invested", slug(amount, coin, year), "index.html")
                write(out, html)
                sitemap_urls.append(f"{SITE}/if-you-invested/{slug(amount, coin, year)}/")

    write(os.path.join(ROOT, "if-you-invested", "index.html"), hub_html(all_pages))
    update_sitemap(sitemap_urls)
    print(f"Generated {len(sitemap_urls)} pages + hub. Sitemap updated.")


if __name__ == "__main__":
    main()
