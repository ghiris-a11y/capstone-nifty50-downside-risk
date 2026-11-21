// Plain-language wording for non-technical readers. Technical names are kept in `tech` so every screen can show
// them in a small "Technical term" line. No result numbers live here: numbers always come from ./data/*.json.
import { GARCH, ML } from "./data";

export interface Term { key: string; plain: string; tech: string; define: string }

export const TERMS: Term[] = [
  { key: "var", plain: "Likely worst daily loss", tech: "Value-at-Risk (VaR)",
    define: "The loss a stock should not go past on most days. At 95% it holds on 19 out of 20 days; at 99% on 99 out of 100 days." },
  { key: "es", plain: "Average loss on the very bad days", tech: "Expected Shortfall (ES)",
    define: "When a day is worse than the likely worst loss, this is how big the loss is on average." },
  { key: "breach", plain: "Day the loss was bigger than the forecast", tech: "Breach / exception",
    define: "A day on which the real loss went past the forecast. We also say the forecast was beaten." },
  { key: "rate", plain: "How often forecasts were beaten", tech: "Breach rate (exception rate) vs nominal level",
    define: "The share of days on which the forecast was beaten. The ideal is 1 in 100 days at 99%, and 5 in 100 at 95%." },
  { key: "kupiec", plain: "Did forecasts fail too often?", tech: "Kupiec test (unconditional coverage)",
    define: "A standard check of whether the forecast was beaten more often, or less often, than it should be." },
  { key: "christoffersen", plain: "Did failures come in clusters?", tech: "Christoffersen test (independence / conditional coverage)",
    define: "A standard check of whether bad days came in bunches instead of being spread out." },
  { key: "basel", plain: "Regulator-style safety check (green = pass)", tech: "Basel traffic-light test (99% only)",
    define: "Banks use this check. Too many beaten days in a year moves a model from green to amber or red." },
  { key: "fz0", plain: "Overall forecast quality score (lower is better)", tech: "FZ0 loss (Fissler-Ziegel) and pinball loss",
    define: "One score that rewards forecasts that are both close and honest about risk. Lower is better." },
  { key: "dm", plain: "Is the difference real, or just luck?", tech: "Diebold-Mariano test",
    define: "A standard check of whether one model's better score is real or could be chance." },
  { key: "vix", plain: "Market fear gauge (India VIX)", tech: "India VIX (implied volatility index)",
    define: "A daily number from the NSE that rises when traders expect big price swings." },
  { key: "garch", plain: "Classic statistics model", tech: "GARCH, EGARCH, GJR-GARCH",
    define: "Models from the 1980s and 1990s that expect calm and wild days to come in spells." },
  { key: "ml", plain: "Machine-learning model that learns from data", tech: "XGBoost, Random Forest, MLP",
    define: "Computer models that find patterns in past data without a fixed formula." },
  { key: "t", plain: "Allows for extreme days", tech: "Student-t distribution",
    define: "A version of a model that expects very big moves to happen more often than a bell curve does." },
  { key: "norisk", plain: "No-risk day", tech: "Forecast quantile at or above zero",
    define: "A day on which a model forecast no loss at all, so any loss beat it." },
  { key: "stress", plain: "Market-wide bad day", tech: "Stress day (Nifty 50 fell 2% or more)",
    define: "A day on which the Nifty 50 index fell by 2% or more. We set this rule before looking at results." },
  { key: "test", plain: "Test period", tech: "Out-of-sample test window",
    define: "The days from 1 January 2024 that the models had never seen. All results come from these days." },
];
export const term = (k: string) => TERMS.find((t) => t.key === k)!;

export const LEVEL_TEXT: Record<string, string> = { "99": "99 out of 100 days", "95": "19 out of 20 days" };
export const IDEAL_TEXT: Record<string, string> = { "99": "1 in 100 days", "95": "5 in 100 days" };

const DETAIL: Record<string, string> = {
  "GARCH-normal": "assumes bell-curve days", "GARCH-t": "allows for extreme days",
  "EGARCH-normal": "bad news counts more; bell-curve days", "EGARCH-t": "bad news counts more; extreme days",
  "GJR-normal": "bad news counts more; bell-curve days", "GJR-t": "bad news counts more; extreme days",
  HistSim250: "repeats the last 250 days", XGBoost: "boosted decision trees", RandomForest: "many decision trees",
  MLP: "small neural network",
};
export function describe(m: string) {
  const kind = GARCH.includes(m) ? "Classic statistics model" : ML.includes(m) ? "Machine-learning model that learns from data" : "Simple benchmark";
  return { kind, detail: DETAIL[m] ?? "" };
}

// Display rule for the good / caution / poor badges, stated on screen: share of stocks that passed
// "Did forecasts fail too often?" (Kupiec, p > 0.05). It is a reading aid, not an extra test.
export type Level = "good" | "caution" | "poor";
export const STATUS_RULE = "Badge = share of the stocks that passed the check “Did forecasts fail too often?”: 90% or more = good, 75–89% = caution, below 75% = poor.";
export const status = (passShare: number): Level => (passShare >= 0.9 ? "good" : passShare >= 0.75 ? "caution" : "poor");

// Plain names for the XGBoost inputs shown in the feature-importance chart.
export const FEATURE_PLAIN: Record<string, string> = {
  vix: "Market fear gauge (VIX) level", vix_chg: "Change in market fear gauge", rv_x_vix: "Recent swings × fear gauge",
  rv_10: "Size of swings, last 10 days", rv_20: "Size of swings, last 20 days", rv_60: "Size of swings, last 60 days",
  ret_l1: "Return yesterday", ret_l2: "Return 2 days ago", ret_l5: "Return 5 days ago", ret_l10: "Return 10 days ago",
  ret_l20: "Return 20 days ago", abs_ret: "Size of yesterday's move", neg_ret: "Yesterday's fall (if any)",
  mdd_60: "Fall from 60-day high", vol_chg_5: "Change in trading volume, 1 week", vol_chg_20: "Change in trading volume, 1 month",
};

// Rewrites technical trace names and notes inside exported Plotly figures into plain words.
const REPLACE: [RegExp, string][] = [
  [/(\S+) (99|95)% VaR \(as return\)/, "$1 likely worst daily loss"],
  [/(\S+) breach \((\d+)\)/, "$1: loss bigger than forecast ($2 days)"],
  [/Market-stress day \(Nifty <= -2%\)/, "Market-wide bad day (Nifty fell 2% or more)"],
  [/Share of test days that are stress days/, "Share of all days that were market-wide bad days"],
  [/^GARCH significantly lower loss$/, "GARCH really better"],
  [/^ML significantly lower loss$/, "Machine learning really better"],
  [/^No significant difference$/, "Could be luck (no real difference)"],
  [/^Nifty 50 cumulative log return \(%\)$/, "Nifty 50 growth since 2015 (%)"],
  [/^India VIX percentile \(0-100, 2015-2026\)$/, "Market fear gauge (India VIX), rank 0–100"],
  [/^(\S+): number of stocks breaching 99% VaR$/, "$1: stocks with a loss bigger than forecast"],
  [/^95% ES$/, "19 out of 20 days"], [/^99% ES$/, "99 out of 100 days"],
  [/^95% VaR\/ES$/, "19 out of 20 days"], [/^99% VaR\/ES$/, "99 out of 100 days"],
  [/^Mean across stocks$/, "Average across stocks"], [/^Median across stocks$/, "Typical stock (median)"],
  [/^Actual daily return$/, "Real daily return"],
];
export function plainText(s: string | undefined) {
  if (!s) return s;
  let out = s;
  for (const [re, to] of REPLACE) out = out.replace(re, to);
  return out;
}
