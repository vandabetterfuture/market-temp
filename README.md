# Market Temperature Dashboard

A mobile-friendly daily market dashboard that scores a custom watchlist using price trend, momentum, RSI and volatility.

## Features

- Buy / Hold / Sell market temperature
- SPY, QQQ and VIX snapshot
- Ranked daily candidates with explainable scores
- $25 starter allocation example
- Automatic weekday refresh through GitHub Actions
- Static hosting through GitHub Pages

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/update_market.py
python -m http.server 8000
```

Open `http://localhost:8000`.

## Deploy with GitHub Pages

In the repository, open **Settings → Pages** and choose:

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/ (root)`

The workflow runs at 13:15 UTC on weekdays and can also be run manually from the Actions tab.

## Important limitations

This is an educational screening tool, not a trading bot or guarantee. The first version uses market-price data only. Earnings, valuation, analyst revisions, news sentiment, premarket data and transaction costs are not yet incorporated.
