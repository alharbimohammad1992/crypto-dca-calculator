# Crypto DCA Calculator & Backtester

A free, single-page web tool that backtests dollar-cost averaging (DCA) on major
cryptocurrencies using **real historical daily prices** from the Binance public
data API. Built as the first tool in a planned cluster of finance/trading
calculators, monetized with Google AdSense.

## What it does
- User picks a coin (BTC, ETH, SOL, BNB, XRP, ADA, DOGE), an amount per buy,
  a frequency (daily / weekly / monthly), and a date range.
- Fetches full daily price history from `data-api.binance.vision` (free, no API
  key, CORS-enabled, paginated 1000 candles/request).
- Computes total invested, current value, profit/loss, ROI.
- Draws a portfolio-growth chart (hand-rolled canvas, zero dependencies).
- Compares the DCA result against a single lump-sum buy at the start.

## Tech
- 100% static: one `index.html` (HTML + CSS + vanilla JS). No build step, no
  framework, no external JS libraries (only a Google Fonts stylesheet).
- Fonts: Sora (UI) + IBM Plex Mono (numbers).
- Data source: Binance klines endpoint `interval=1d`.

## Run locally
Just open `index.html` in a browser, or serve it:
```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deploy (free)
Target: Cloudflare Pages.
- Option A (simple): Upload the folder via dash.cloudflare.com → Workers & Pages
  → Create → Pages → Upload assets.
- Option B (git): push this repo to GitHub, connect it in Cloudflare Pages.
  Build command: none. Build output directory: `/` (root).

Note: the `*.pages.dev` URL works for testing but AdSense requires a custom
domain (.com). Buy/connect the domain only after deploying and verifying.

## SEO notes (already in index.html)
- `<title>` and meta description target "crypto DCA calculator".
- H1 + explanatory content + FAQ block (needed for AdSense approval).
- TODO before launch: add favicon, Open Graph tags, sitemap.xml, robots.txt,
  and JSON-LD FAQ schema (see TODO.md).

## Roadmap / next tools in the cluster
1. DCA Calculator (this) — primary keyword, low competition.
2. Crypto profit / PnL calculator.
3. Compound growth calculator.
4. (later, harder) Liquidation price calculator.

## Important
This is an educational tool. It does not give financial advice and does not
account for trading fees or taxes.
