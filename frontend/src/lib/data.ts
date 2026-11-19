import { useEffect, useState } from "react";

// Every data file is fetched with a relative path so the build works under any base path.
const cache = new Map<string, Promise<unknown>>();

export function fetchJson<T>(path: string): Promise<T> {
  const url = `./data/${path}`;
  if (!cache.has(url)) {
    cache.set(
      url,
      fetch(url).then((r) => {
        if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
        return r.json();
      }),
    );
  }
  return cache.get(url) as Promise<T>;
}

export function useJson<T>(path: string | null) {
  const [state, setState] = useState<{ data?: T; error?: string; loading: boolean }>({ loading: !!path });
  useEffect(() => {
    if (!path) return;
    let alive = true;
    setState({ loading: true });
    fetchJson<T>(path)
      .then((data) => alive && setState({ data, loading: false }))
      .catch((e: Error) => alive && setState({ error: e.message, loading: false }));
    return () => {
      alive = false;
    };
  }, [path]);
  return state;
}

export const GARCH = ["GARCH-normal", "GARCH-t", "EGARCH-normal", "EGARCH-t", "GJR-normal", "GJR-t"];
export const ML = ["XGBoost", "RandomForest", "MLP"];
export const ORDER = [...GARCH, "HistSim250", ...ML];
export const COLOURS: Record<string, string> = {
  "GARCH-normal": "#fcae91", "GARCH-t": "#fb6a4a", "EGARCH-normal": "#ef3b2c", "EGARCH-t": "#cb181d",
  "GJR-normal": "#a50f15", "GJR-t": "#67000d", HistSim250: "#7f7f7f",
  XGBoost: "#08519c", RandomForest: "#3182bd", MLP: "#6baed6",
};
export const family = (m: string) => (GARCH.includes(m) ? "GARCH" : ML.includes(m) ? "ML" : "Benchmark");
export const pct = (v: number | null | undefined, d = 2) => (v == null ? "n/a" : `${(100 * v).toFixed(d)}%`);
export const num = (v: number | null | undefined, d = 4) => (v == null ? "n/a" : v.toFixed(d));

export interface SummaryRow {
  model: string; alpha: number; exc_rate: number; pass_kupiec: number; pass_cc: number; green99: number | null;
  pinball: number; fz0: number; es_ratio: number; fz0_median_stocks: number; fz0_daily_median: number; norisk_days: number;
}
export interface SummaryFile { labels: Record<string, string>; default: string; summary: Record<string, SummaryRow[]> }
export interface BacktestRow {
  ticker: string; model: string; alpha: number; n: number; exceptions: number; exc_rate: number; kupiec_p: number;
  ind_p: number; cc_p: number; pass_kupiec: boolean; pass_cc: boolean; basel_green_share: number | null;
  pinball: number; fz0: number; actual_over_expected_es: number | null; fz0_median: number; norisk_days: number;
}
export interface DmCount { model: string; garch: number; ml: number; none: number }
export interface Meta {
  snapshot_utc: string; data_first: string; data_last: string; test_start: string; n_stocks: number; n_excluded: number;
  train_end: string; val_end: string; hike_date: string; macro_note: string; approval_note: string;
  results_generated_utc: string; live_as_of?: string; live_generated_utc?: string; exported_utc?: string;
}
