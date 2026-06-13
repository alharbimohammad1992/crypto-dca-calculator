# CLAUDE.md — Project context for Claude Code

## Project
Crypto DCA Calculator — a static single-file web tool (`index.html`) that
backtests dollar-cost averaging on crypto using real Binance historical prices.
This is the first of a planned cluster of finance/trading calculator tools,
monetized via Google AdSense. SEO and page speed are top priorities.

## Owner context
- Solo developer, strong Python background, comfortable with code.
- Goal: rank for "crypto dca calculator" and related long-tail keywords, get
  organic traffic, get AdSense approved, earn first ad revenue.
- Budget: free tools only. Hosting = Cloudflare Pages. The only paid item is a
  domain (~$10/yr) bought later.

## Hard constraints — do not break these
- **Keep it a single static `index.html`** unless explicitly asked to add a
  build step. No React, no bundler, no npm dependencies. The whole appeal is
  speed and simplicity (good Core Web Vitals = better SEO).
- **No external JS libraries.** The chart is hand-rolled on `<canvas>`. Do not
  swap it for Chart.js etc. without being asked.
- **No localStorage / sessionStorage** assumptions; keep state in JS variables.
- **Latin numerals always.** Inputs are `type="text"` on purpose (native
  date/number inputs render Arabic-Indic digits on Arabic-locale browsers).
  There is a `toLatin()` helper that normalizes Arabic/Persian digits before
  parsing. Keep this.
- **Data source = Binance** `data-api.binance.vision` klines, `interval=1d`,
  paginated. Free, no key, CORS-enabled. Do not reintroduce CoinGecko (its free
  tier caps history at 365 days — that bug was already fixed).

## Code conventions
- Plain ES, no transpilation needed. Keep functions small and readable.
- Money formatting via `fmtUSD`, percentages via `fmtPct`.
- Coin → Binance symbol map is `SYMBOLS` (e.g. bitcoin → BTCUSDT).
- Price lookup uses `priceAt(prices, ts)` (binary search, nearest <= ts).

## When adding a new tool/page
- Each tool = its own folder with an `index.html` (e.g. `/profit-calculator/`).
- Reuse the same design tokens (CSS variables in `:root`) for visual
  consistency across the cluster.
- Every tool page needs: unique `<title>`, meta description, an H1, real
  explanatory content + FAQ (AdSense requirement), and the disclaimer.

## Before any launch / deploy
See `TODO.md`. Priorities: favicon, OG tags, sitemap.xml, robots.txt, JSON-LD
FAQ schema, and a privacy policy page (required for AdSense).

## Testing
No test framework. To verify: `python3 -m http.server 8000` and click through
each coin + frequency + a long date range (e.g. 2018-01-01 to today). Confirm
numbers are Latin, the chart renders, and the DCA vs lump-sum verdict shows.
