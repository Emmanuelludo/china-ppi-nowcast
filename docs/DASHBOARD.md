# Live PPI dashboard

**[Open the dashboard](https://china-ppi-nowcast-live.clumsy-cyclic-aqua.chatgpt.site).**

The dashboard is deployed with Sites. GitHub stores the authoritative models,
immutable forecasts and daily output. It does not require enabling GitHub Pages.
The Site currently uses owner-only access.

The first screen shows the latest available forecast month, XGBoost, CatBoost,
LightGBM, HistGradientBoosting and product ridge. The median describes these five
estimates; it is not a selected ensemble. Model range is not a prediction interval.
Forest, sector-first and economic / ML hybrid estimates remain in the comparison
table. The uncalibrated circulation-price tracker appears separately.

Choose a month, price timing and full or stable product panel. Unsupported stable
panels are disabled rather than shown as empty forecasts. October is labelled
pending while September remains visible until a valid October information set exists.

Each forecast has its own exact frozen timestamp, training range, source windows,
fitted version and archive link. Displayed numbers retain full precision in the
data feed and round to three decimals in the interface. All headline forecasts
are month-on-month percentages; errors and attributions are percentage points.

## Data updates

The existing daily nowcast workflow generates `reports/dashboard_data.json` and
`reports/dashboard.html` through `china_ppi_nowcast.dashboard`. The live Site reads
the JSON directly from the public repository on opening, on Refresh data, and
every five minutes while visible. Existing monthly forecasts remain immutable.
No separate model fitting, API credentials or duplicate automation is used by
the dashboard.

The page includes a saved snapshot so that it remains readable when GitHub is
temporarily unavailable. A failed refresh displays the snapshot date and a clear
message. Invalid or older live data never replace the displayed snapshot.

The source template is `src/china_ppi_nowcast/dashboard_template.html`; interface
logic is `dashboard_script.js`; forecast extraction is `dashboard.py`. The host
and JSON feed addresses are recorded in `config/dashboard.json`.

For design updates, regenerate the dashboard, copy `reports/dashboard.html` to the
Site's `dist/index.html`, and publish a new Site version. Routine forecast updates
only need the existing daily GitHub workflow. Historical accuracy remains
pseudo-real-time; prospective evaluation continues independently.
