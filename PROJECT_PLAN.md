# PROJECT_PLAN.md — Capstone Phase 2 (fast track, no fixed dates)

Work through the phases in order. Each phase has a "done when" check, so you can stop and resume between your other projects without losing your place. Long computing runs happen unattended; your own effort is mostly pasting a prompt, checking the result, and committing.

## 1. Locked decisions
| Item | Decision |
|---|---|
| Sample | Balanced panel of about 40–45 stocks with full price history from 2015; universe fixed at one date; newer listings (Jio Financial, Eternal) dropped |
| Test window | 1 Jan 2024 to end of Nov 2026 (includes the 7 Oct 2026 repo hike to 5.50% and the shift to tightening) |
| Backtests | Basel traffic light on 99% VaR only; Kupiec and Christoffersen at 95% and 99% |
| Target | Next-day realised return; rolling 250-day historical simulation becomes a benchmark model, not the label |
| Chapter 1 macro narrative | Rewritten for the tightening cycle (repo 5.50%) |
| References | Thenmozhi & Chandra working paper details fixed; Buczynski & Chlebus pages fixed; Behera et al. described correctly (AdaBoost best); Ali & Dembo (2025) added |
| Automation | GitHub Actions, cron 13:30 UTC (7:00 PM IST) Mon–Fri, runs `update_data.py` |
| Dashboard | Static React + TypeScript + Vite + Tailwind app reading JSON files that the pipeline and GitHub Action export; no backend; hosted on GitHub Pages |
| Hosting | GitHub Pages only (code, frozen data, live data and dashboard in one repo); the Action rebuilds and redeploys every weekday |

## 2. Things to watch (short list)
1. **GitHub cron is in UTC.** `30 13 * * 1-5` = 7:00 PM IST on weekdays. Runs can start a few minutes late. Give the workflow `permissions: contents: write` or the commit-back step will fail.
2. **Commit only small live files.** Keep `data/frozen/` (the report snapshot) separate from `data/live/` (the daily feed). Never let the Action touch `data/frozen/`.
3. **Report numbers come from the frozen snapshot.** The live feed drives the dashboard's "latest risk" tab only. Say this in the report so numbers stay reproducible.
4. **Yahoo is unofficial.** `yfinance` can break or throttle. The validation step and a failure alert (GitHub emails you when a scheduled run fails) cover this.
5. **Hosting: GitHub Pages only.** The dashboard is a static build (`dist/`) plus JSON, so there is no server, no cold start and no third-party keys or trials. Watch-outs: Vite needs `base` set to `/<repo-name>/`, the app must fetch `./data/...` with relative paths, and nested routes break on refresh on GitHub Pages, so use `HashRouter`. Free GitHub Pages normally needs a public repository (check your account's current terms), so keep only data you are comfortable publishing there and respect Yahoo's terms for any raw prices you publish.
6. **Template received.** Teacher's Phase 2 format (same look as Phase 1, with no certificate and no acknowledgement): Cover; 1 Introduction; 2 Literature Review; 3 Research Methodology; 4 Data Collection; 5 Data Analysis and Interpretation; 6 Recommendations; 7 Conclusion; 8 References (minimum 10, APA); 9 Appendices. See section 2A for what goes in each. Put the Phase 1 PDF in `report/template/` so Claude Code can copy its layout and logo.
7. **Ali & Dembo (2025):** the preprint is at preprints.org/manuscript/202509.0997. Open the page and copy the exact title, authors and date before citing.

## 2A. Report structure (teacher's template) and what each part must contain
This is an MBA Business Analytics capstone, so most of the pages and marks should go to analysis, interpretation and actionable recommendations, not theory. Target split: Chapters 1-3 about 25%, Chapters 4-5 about 40%, Chapter 6 about 20%, rest 15%.

| Part | Required by template | What to write |
|---|---|---|
| Cover page | Title, student name / roll no., MBA BA, faculty guide, institute | Same layout as Phase 1 cover with the logo. **Roll no. 021331025144** (Phase 1's cover printed 0211331025144, a typo, so do not copy it). Semester: Phase 1 said II; use Semester III for Phase 2 unless the guide says otherwise. No certificate, no acknowledgement. |
| 1 Introduction | Industry overview, structure, SWOT, problem statement, scope | Industry = Indian equity markets and market risk management. Structure = NSE, SEBI, Nifty 50 composition and sectors, participants (FPIs, DIIs, retail, brokers, banks, AMCs) and how VaR is used (margins, limits, capital). SWOT of downside-risk management practice in Indian equities (table). Problem in business terms: wrong risk estimates mean wrong margins, capital and position limits. Scope: 40-45 stocks, daily data 2015 to Nov 2026, one-day horizon, secondary data. |
| 2 Literature Review | Papers, research gap, question, objectives, hypotheses | Group by theme (risk measures and backtesting; GARCH evidence in India; ML and hybrids; India VIX and macro). At least 10 verified references. End with gap table, research questions RQ1-RQ4, objectives, hypotheses H1-H4. |
| 3 Research Methodology | Design, sources, sampling, sample size, techniques and justification | Quantitative, empirical, ex-post forecasting design. Sampling: purposive (judgemental) balanced panel from the fixed Nifty 50 universe; state N stocks and N stock-days. Table "technique, why chosen, what it answers" for every method (GARCH family, Student-t, XGBoost, RF, MLP, historical simulation, Kupiec, Christoffersen, Basel zones at 99%, FZ0, Diebold-Mariano, SHAP, VIX-quartile regimes). |
| 4 Data Collection | Data type, sources, dataset description, descriptive statistics | Secondary, quantitative, time-series panel. Source table, snapshot date and hash, variable dictionary summary, descriptive statistics per stock and sector (mean, SD, skewness, kurtosis, Jarque-Bera, ADF, ARCH-LM), with a short reading of each. |
| 5 Data Analysis and Interpretation | Cleaning, statistics, tables, charts, analysis, interpretation, findings | Cleaning log, model results, backtests, ES evaluation, regimes (including the Oct 2026 tightening), ablation, sector view. Every table and chart is followed by "What this means" in plain business language. Findings list ties back to H1-H4. |
| 6 Recommendations | Business recommendations, feasibility and viability, expected benefits | See below. |
| 7 Conclusion | Summary of findings, future research | One sentence per research question, contribution, limitations, future work. |
| 8 References | Minimum 10, APA | Verified list only; mark anything unverified. |
| 9 Appendices | Questionnaire, supporting tables, additional analysis | Questionnaire: **not applicable** because the study uses secondary market data only (say this in one line, with the reason). Supporting tables: per-stock results, hyperparameters, GARCH estimates. Additional analysis: robustness, ablation detail. Also the variable dictionary and the code and GitHub Action description. |

**Recommendations chapter (the part that scores as "actionable"):**
- A decision table with columns: user (bank risk desk, broker margin team, portfolio manager, retail or fintech app, regulator or exchange) | recommended model or rule | evidence (exact figure from the results) | expected benefit | viability.
- Business recommendations drawn directly from the findings: model choice by use case and by regime, a switching or blending rule keyed to India VIX, retrain and monitoring cadence (exception clustering as an early warning), sector-specific guidance, and whether macro variables are worth the data cost.
- Feasibility and viability: data cost (free daily data versus licensed), skills and tooling (Python, scheduled updates, dashboard), compute time (from the real run), model governance and explainability (SHAP), regulatory fit (VaR/ES backtesting norms), and key risks.
- Expected benefits: quantified only from outputs, for example the change in exception rate, the capital buffer difference implied by average VaR levels, and fewer clustered breaches. State assumptions clearly.

## 3. Phases

### Phase A — Pilot and approval
Run the pipeline on RELIANCE.NS, HDFCBANK.NS, INFY.NS with the extended window, prepare a one-page results summary, and get Dr. Pardeshi's approval for the balanced panel and the extended window. Ask for the template in the same meeting.
**Done when:** you have the pilot summary and the guide's approval (written or by message).
Prompts: P0, P1. You can also run P7 here, since the front chapters need no results.

### Phase B — Data: universe, frozen snapshot, automation
Build the balanced panel, freeze the historical dataset with hashes, and set up the GitHub Action.
**Done when:** `config/universe.csv` lists 40–45 stocks; `data/frozen/` has a manifest; one manual workflow run (workflow_dispatch) succeeds and commits.
Prompts: P2, P3.

### Phase C — Full execution (mostly unattended)
Make the pipeline parallel and resumable, then run all three feature sets (price, price+vix, price+vix+macro) over the full panel.
**Done when:** all CSVs are in `outputs/tables/` and no ticker failed without a log entry.
Prompts: P4.

### Phase D — Figures, dashboard, chapters
Generate the Plotly figures, build the React dashboard from the same figure JSON, then draft the analysis, recommendations and conclusion chapters from the real CSVs.
**Done when:** the figures exist, the dashboard runs locally (`npm run dev`) and (optionally) online, chapters are drafted with sources for every number.
Prompts: P5, P6, P8.

### Phase E — Assembly and submission
Assemble the report in the teacher's format, run the QA check, final proofread, submit.
**Done when:** final PDF exported, QA report clean.
Prompts: P9, P10.

## 4. If you run short of time (minimum viable path)
1. Phases A, B (without the Action), C, then P5 (figures) and P7 (chapters), then P8.
2. Dashboard: build once and run it locally (`npm run dev` or `npm run preview`) from the frozen JSON; the report does not depend on it.
3. Skip the price+vix feature set; keep price-only and price+vix+macro (the ablation then has two points).
4. Keep the Action as a described extension if it is not finished.

## 5. Claude Code prompts
Run in order from the project root in the VS Code terminal (`claude`). Put `CLAUDE.md` and `nifty50_var_pipeline.py` in the folder first.

### P0 — Scaffold
```
Read CLAUDE.md. Create the folder structure it describes, a requirements.txt with pinned versions (pandas numpy scipy arch xgboost scikit-learn shap plotly kaleido joblib pyarrow pytest yfinance), a .gitignore (ignore data/raw, outputs/models, .venv), and a README.md with venv setup steps. Do not touch nifty50_var_pipeline.py. Initialise git and make the first commit. Create one trivial pytest, then run pytest -q and python nifty50_var_pipeline.py --demo and report the output.
```

### P1 — Pilot on 3 tickers, with the pilot summary and guide pitch written by Claude Code
```
Run the pipeline on RELIANCE.NS, HDFCBANK.NS, INFY.NS with --features price+vix+macro and the latest available test end (use the last date Yahoo returns). If a step fails, show the error and propose an exact replacement block; do not rewrite the file. Time the run and keep outputs. Then read outputs/summary_price_vix_macro.csv, regime_results_price_vix_macro.csv and diebold_mariano_price_vix_macro.csv and create, using only numbers from those files:
(1) report/pilot_summary.md with: setup (tickers, data dates, train/validation/test windows, models); a table of exception rate at 95% and 99% per model against the nominal 5% and 1%; Kupiec and Christoffersen pass rates; Basel Green share at 99% only; mean pinball and FZ0 loss; mean FZ0 by India VIX quartile; and, if the test window covers it, a separate line for the period after the 7 Oct 2026 repo hike.
(2) Two charts in outputs/figures/pilot/ (PNG at 300 DPI, GARCH red, ML blue): exception rate by model with the nominal line, and VaR forecast vs actual returns with breach markers for RELIANCE.NS.
(3) report/pilot_pitch.docx (one to two pages, Times New Roman, in the look of the Phase 1 report from report/template/ if present): purpose; what was run; the results table and the two charts; three to five plain-language observations that follow strictly from the numbers (for example which family is closer to nominal exception rates, whether ML helps in the high-VIX quartile); problems found (failed GARCH fits, exception rates far from 5% or 1%, data issues); a caution that three stocks are a pilot and not a conclusion; and a closing box "Approval requested from Dr. Pardeshi": (a) balanced panel of 40-45 stocks, (b) test window extended to Nov 2026, (c) Basel zones at 99% only and the historical-simulation benchmark instead of the rolling-quantile target, (d) the Phase 2 template. Also export it to PDF.
Do not invent or round numbers beyond what the CSVs contain, do not state conclusions the pilot cannot support, and list anything you are unsure about at the end of your reply.
```

### P2 — Balanced panel and frozen snapshot
```
Write src/build_universe.py, src/download_history.py and src/validate_data.py. (1) Create config/nifty50_dec2025_candidates.csv (ticker, name, sector) for the December 2025 Nifty 50; ask me to confirm any name you are unsure of instead of guessing. (2) build_universe.py: download history from 2015-01-01, keep only stocks whose first valid price is on or before 2015-01-15 with no gap longer than 10 trading days; write config/universe.csv (ticker, sector, first_date, n_days) and config/universe_excluded.csv with reasons; print the count; flag Tata Motors and HDFCBANK.NS corporate actions. (3) download_history.py: for every universe ticker plus ^NSEI, ^INDIAVIX, INR=X download adjusted daily OHLCV from 2015-01-01 to the latest available date, with retries, 1-second delay, and logging to data/logs/. (4) validate_data.py: no nulls, no non-positive prices, no duplicate dates, flag daily moves above 20%, and compare adjusted close against a second download for 5 sample tickers. (5) Save one parquet per ticker in data/frozen/, a manifest.csv with SHA-256 hashes, row counts and the snapshot date, and validation_report.md; make data/frozen read-only. (6) Create data/raw/repo_rate.csv, cpi.csv, iip.csv templates (date,value) and tell me exactly which official RBI and MoSPI pages to fill them from; do not invent values.
```

### P3 — GitHub Actions automation
```
Write src/update_data.py and .github/workflows/daily_update.yml. update_data.py: read config/universe.csv; for each ticker plus ^NSEI, ^INDIAVIX and INR=X, load its rows from data/live/prices_live.csv (long format: date, ticker, open, high, low, close, adj_close, volume), fetch yfinance data from 5 days before the last stored date to today, and validate before appending: block nulls, zero or negative prices, duplicate dates; quarantine any one-day move above 20% to data/live/quarantine.csv (suspected unadjusted split) instead of appending; compare the 5 overlapping days of adjusted close with stored values and flag any difference above 0.5% as a possible corporate action in data/logs/update_log.csv; treat a missing date as an error only if Nifty has data that day and the ticker does not. Append only new, valid rows. Never read or write data/frozen/. After appending, compute the latest one-day-ahead 95% and 99% VaR and ES per stock with a GJR-GARCH(1,1) Student-t fitted on the last 1,500 days and save outputs/live/latest_risk.csv. Exit with a non-zero code if any ticker failed validation so the run fails visibly. The workflow: cron '30 13 * * 1-5' (7:00 PM IST on weekdays) plus workflow_dispatch; permissions contents: write; Python 3.11 with pip caching; run update_data.py; commit data/live, data/logs and outputs/live back to the repo with the github-actions bot only if files changed, with a "[skip ci]" message. Add a short README section explaining how to trigger it manually and where the logs are.
```

### P4 — Speed up and run (surgical)
```
Without rewriting nifty50_var_pipeline.py, propose exact replacement blocks to: (1) add --n-jobs and process tickers in parallel with joblib; (2) read prices from data/frozen/*.parquet when --frozen is set instead of calling yfinance; (3) write one results file per ticker to outputs/tables/by_ticker/ and skip tickers already done (resume); (4) take the test end from --test-end; (5) merge per-ticker files into the existing summary, regime and Diebold-Mariano outputs at the end. Keep all existing function and column names. Apply the blocks, run --demo, rerun the 3 pilot tickers and confirm results match the pilot within numerical tolerance. Estimate the full-run time for the universe from the pilot timing, then run all three feature sets one after another with --frozen --n-jobs set to the available cores, logging progress to data/logs/run.log. Do not stop for questions unless a ticker fails repeatedly; list failures at the end.
```

### P5 — The figures
```
Write src/make_figures.py that reads only outputs/tables/*.csv and data/frozen/*.parquet and produces, with Plotly (PNG at 300 DPI via kaleido plus interactive HTML) in outputs/figures/: (1) Nifty 50 and India VIX dual-axis with shaded regimes and the 7 Oct 2026 repo hike marked; (2) return-distribution grid by stock; (3) VaR forecast vs actual returns with breach markers for a selectable stock; (4) exception-rate heatmap stocks x models at 99%; (5) performance by VIX quartile (grouped bars with error bars); (6) SHAP importance for XGBoost (compute and save SHAP values in a separate script if missing); (7) Kupiec vs Christoffersen scatter; (8) ES calibration (actual-over-expected tail loss); (9) sector risk box plots; (10) leaderboard table figure. GARCH = red palette, ML = blue palette, min font 10pt, labelled axes with units. Make every figure a function returning a Plotly figure object (so the dashboard JSON export can reuse it) and write captions.md with one factual caption per figure drawn from the data, with no interpretation the CSVs do not support.
```

### P6 — Dashboard (static React on GitHub Pages)
```
Build the dashboard as a static React app hosted on GitHub Pages. No backend.
(1) src/export_dashboard_json.py: read outputs/tables/*.csv, data/live/prices_live.csv, outputs/live/latest_risk.csv and the figure functions in src/make_figures.py; write JSON to frontend/public/data/: summary.json (KPIs), backtest.json, regime.json, stocks.json, daily_var_<ticker>.json, live_risk.json, meta.json (snapshot date, last live update) and figures/<name>.json using fig.to_json().
(2) frontend/: React + TypeScript + Vite + Tailwind with react-router using HashRouter (BrowserRouter breaks on refresh on GitHub Pages). Tabs: Overview (KPI cards: best model by joint VaR-ES loss, Kupiec and Christoffersen pass rates, Basel Green share at 99%; filters for sector, model family, VaR level), Model comparison, Regimes, Stock drill-down (stock and model selectors, VaR vs returns with breaches), Feature importance, Live risk (latest prices, India VIX, one-day 95% and 99% VaR and ES; clearly labelled as the live extension, not the report results), About (methodology, snapshot date, limitations). Render figures with react-plotly.js using a lazy-loaded Plotly bundle that reads figures/*.json. Include loading and empty states, responsive layout readable on a projector, red = GARCH and blue = ML, no placeholder numbers.
(3) Vite config and data paths: set base in vite.config.ts to '/<repo-name>/' (ask me for the repository name), and fetch every data file with relative paths such as './data/summary.json' (never absolute URLs or '/data/...'), so the same build works locally and on GitHub Pages.
(4) Surgically extend .github/workflows/daily_update.yml so that, after update_data.py, it: runs export_dashboard_json.py; commits frontend/public/data back to the repo; runs 'npm ci' and 'npm run build' in frontend/; and deploys frontend/dist to GitHub Pages using a deployment action (the official actions/upload-pages-artifact with actions/deploy-pages, or peaceiris/actions-gh-pages pushing to the gh-pages branch). Add the permissions the chosen action needs (contents: write, plus pages: write and id-token: write for the official action). Cache npm. Keep the failure behaviour: a failed validation fails the run.
(5) Add README notes: enable GitHub Pages in the repository settings (source: GitHub Actions or the gh-pages branch), the final URL, and local 'npm run dev' and 'npm run preview'. Run tsc --noEmit and npm run build, fix errors, and check that dist/index.html references assets under the base path.
```

### P7 — Front chapters (no results needed)
```
Put the Phase 1 PDF in report/template/ first. Read CLAUDE.md and the report structure in PROJECT_PLAN.md section 2A. Write report/chapters/01_introduction.md, 02_literature_review.md, 03_methodology.md and 04_data_collection_frame.md in the teacher's Phase 2 format (no certificate, no acknowledgement). Chapter 1: industry overview of Indian equity markets, market structure (NSE, SEBI, Nifty 50 and sectors, participants, how VaR and ES are used for margins, limits and capital), a SWOT table for downside-risk management in Indian equities, problem statement in business terms, and scope (40-45 stock balanced panel, daily data 2015 to Nov 2026, one-day horizon, secondary data). Update the macro narrative to the RBI's 7 Oct 2026 hike to 5.50% and the shift to calibrated tightening. Chapter 2: thematic review with at least 10 sources, a research gap table, RQ1-RQ4, objectives and hypotheses H1-H4. Chapter 3: research design, sampling technique (purposive balanced panel) and sample size (leave N as a placeholder filled from config/universe.csv), data sources, and a table of every technique with why it was chosen and what it answers. Chapter 4 frame: type of data, sources table, dataset description; leave descriptive-statistics tables to be generated from outputs. Rules: every statistic about markets or papers needs a source in report/chapters/sources.md with URL and access date; mark anything unverifiable [UNVERIFIED]; no invented numbers; keep theory short, around a quarter of the report. Use the Phase 1 verified fixes for references (Thenmozhi & Chandra NSE WP/9/2013 and Decision 42(1) 33-55, doi 10.1007/s40622-014-0070-0; Buczynski & Chlebus, Computational Economics 63(5) 1949-1979, doi 10.1007/s10614-023-10390-7; Behera et al., Eng. Appl. of AI 120, 105843, with AdaBoost as best model; the GINN arXiv:2410.00288 with its real authors Xu, Liechty, Benthall, Skar-Gislinge, McComb; Sahiner, McMillan & Kambouroudis (2023), Journal of Economics and Finance 47(3), 723-762, doi 10.1007/s12197-023-09629-8, ten Asian markets, not Physica A and not single-author). Treat Mishra & Mishra (2024), Xu et al. (2024), Al-Najjar & Al-Najjar (2025), Susruth (2017), Tan (2025), Kumar et al. (2024) and Patel & Kumar (2025) as [UNVERIFIED] until I paste a working link or DOI for each; do not cite their findings in the text until then). Ask me to paste the Ali & Dembo (2025) title and authors from the preprint page.
```

### P8 — Analysis, recommendations, conclusion (from real results)
```
Using only files in outputs/tables/ and outputs/figures/, write report/chapters/04_data_collection_stats.md (descriptive statistics tables with a short reading each), 05_analysis_interpretation.md, 06_recommendations.md, 07_conclusion.md and 09_appendices.md. Chapter 5 sections in this order: data cleaning and preprocessing log; statistical analysis (GARCH estimates, ML tuning); tables, charts and graphs (embed the figures with numbered captions: Figure 5.1, Table 5.1); analysis of results (VaR backtests with Kupiec, Christoffersen and Basel zones at 99%, ES evaluation, Diebold-Mariano, VIX-quartile regimes including the post-7-Oct-2026 period, ablation of VIX and macro, sector results); interpretation and findings. After every table or chart add a short "What this means" paragraph in business language, and give every finding the exact number and its source CSV in an HTML comment. Mark H1-H4 supported, partly supported or rejected strictly from the data. Chapter 6: build the decision table (user | recommended model or rule | evidence | expected benefit | viability) for a bank risk desk, a broker margin team, a portfolio manager, a retail or fintech app and an exchange or regulator; add feasibility and viability (data cost, skills, compute time from data/logs/run.log, governance and explainability, regulatory fit, risks) and expected benefits computed from the outputs with assumptions stated (for example capital buffer implied by average VaR, exception-rate gap to nominal, clustered breaches avoided). Do not recommend a model the data does not support; if ML lost, say so and recommend accordingly. Chapter 7: one sentence per research question, contribution, limitations, future research. Appendices: state the questionnaire is not applicable because the study uses secondary data; add per-stock results, hyperparameters, GARCH estimates, robustness, variable dictionary, code and GitHub Action description. Do not invent any statistic.
```

### P9 — Assemble the Word report in the Phase 1 form
```
Open report/template/Phase1_Report.pdf and copy its look: Times New Roman, centred bold title page with the ITM logo (extract it from the PDF), the "Submitted by" block (guide name and designation; student name, roll no., programme MBA, batch, semester; roll no. 021331025144, Semester III, Batch 2025-27, specialisation MBA Business Analytics), table of contents with page numbers, chapter headings in capitals, page numbers bottom right. Skip the certificate and the acknowledgement. Use python-docx to build report/Phase2_Report.docx from report/chapters/*.md in this order: Cover, Table of Contents (plus lists of tables and figures), 1 Introduction, 2 Literature Review, 3 Research Methodology, 4 Data Collection, 5 Data Analysis and Interpretation, 6 Recommendations, 7 Conclusion, 8 References (APA, minimum 10), 9 Appendices. Insert figures from outputs/figures/ at 300 DPI with numbered captions, tables as real Word tables, and cross-reference every figure and table in the text. Check that every figure referenced exists, every number in the text appears in a CSV, and no [FILL] or [UNVERIFIED] markers remain without my approval. Export a PDF as well and report page count per chapter so I can check the analysis chapters carry most of the pages.
```

### P10 — Final QA
```
Run pytest -q; rerun the pipeline on 2 tickers from data/frozen and confirm the results match outputs/ exactly (fixed seeds); verify manifest hashes in data/frozen; confirm the GitHub Action's last run succeeded and that data/frozen is unchanged in git history; list any ticker with fewer than 500 test days or failed model fits; list every number in the report with its source file; confirm the report has at least 10 verified references and no certificate or acknowledgement page. Write QA_report.md.
```

## 6. Checklist
- [ ] A: pilot summary, guide approval, template received
- [ ] B: universe built, frozen snapshot hashed, Action runs manually and commits
- [ ] C: full run complete for all feature sets
- [ ] D: figures, React dashboard, chapters, references fixed
- [ ] E: assembled report, QA clean, final PDF, submitted

## 7. Viva questions to prepare
1. Why a balanced panel, and how does it bias results (survivorship)?
2. Why is the Basel traffic light used only at 99%?
3. How do you avoid look-ahead bias (shifted features, chronological split, release-lagged macro)?
4. Why pinball and FZ0 losses, and what does Diebold-Mariano add?
5. What did the tightening period show?
6. Where did ML lose, and why might that be?
7. What are the limits of 99% backtests on roughly 700 test days?
8. How reproducible is the work (frozen data, hashes, seeds), and how does the live feed differ from the report data?
