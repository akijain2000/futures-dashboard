# Futures Dashboard

A live futures contract dashboard pulling data from Barchart — featuring interactive charts, expiry countdowns, and a full contract summary table.

## Contracts Tracked

| Symbol | Name | Exchange |
|--------|------|----------|
| CKM26 | ICE EUA Jun '26 | ENDEX |
| CKZ26 | ICE EUA Dec '26 | ENDEX |
| CLK26 | WTI Crude Oil May '26 | CME |
| NGK26 | Natural Gas May '26 | CME |
| QAM26 | Brent Crude May '26 | ICE |

## Features

- **Live quotes** — last price, change, % change, 52W high/low
- **Interactive charts** — line, candlestick, OHLC, volume (90-day history)
- **Support & resistance** overlays on charts
- **Expiry countdown** — progress bars with color alerts (red < 30d, yellow < 90d)
- **Summary table** — all key metrics in one view
- **Mini charts** — side-by-side history for all contracts
- **Auto-refresh** every 60 seconds

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:5050](http://localhost:5050)

## Data Source

All data is scraped from [barchart.com](https://www.barchart.com). Historical data uses Barchart's timeseries proxy endpoint. If live data is unavailable, realistic fallback history is generated for demo purposes.
