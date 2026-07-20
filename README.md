# Market Temperature — Phase 2

A mobile-friendly daily market intelligence dashboard hosted on GitHub Pages.

## Phase 2 features

- Overview, Candidates, News, Portfolio and History tabs
- Buy / Hold / Sell market temperature
- RSI, volatility-based risk level and stronger candidate details
- Sector relative-strength rankings
- Latest headlines for selected tickers
- Editable holdings in `config.json`
- Portfolio value and gain/loss calculations
- 90-day market-score history
- Automated weekday refresh with GitHub Actions

## Install

```bash
unzip market-temp-phase2.zip
cd market-temp
cp -R /path/to/market-temp-phase2/. .
git add .
git commit -m "Add Phase 2 dashboard"
git push origin main
```

## Publish

GitHub → Settings → Pages → Deploy from branch → `main` → `/ (root)`.

Then run **Actions → Update market dashboard → Run workflow**.

Your site:

`https://vandabetterfuture.github.io/market-temp/`

## Portfolio setup

Edit `config.json`:

```json
{
  "starting_cash": 25,
  "holdings": [
    {"ticker": "SCHG", "shares": 0.1, "cost_basis": 3.00}
  ]
}
```

`cost_basis` is the total amount paid for that holding, not the per-share price.

## Important

This is a rules-based educational research tool. It does not guarantee profits and cannot reliably turn $25 into $2,500 in one year.
