import { useEffect, useMemo, useState } from "react";
import Figure, { chartFont, isPhone, type FigJson } from "../components/Figure";
import Plot from "../components/Plot";
import { Empty, ErrorBox, Loading, Pills, Section, Select, StockBadge, Table } from "../components/ui";
import { Experts, HowToRead, Means, ModelName, Status, Takeaway } from "../components/plain";
import { COLOURS, fetchJson, GARCH, ML, num, ORDER, pct, useJson, type BacktestRow, type Meta } from "../lib/data";
import { LEVEL_TEXT } from "../lib/plain";
import { useStore } from "../lib/store";

// Sector medians of the per-stock average 99% VaR (in %), read from the exported Figure 9 data; sorted low to high.
function sectorMedians(f: FigJson): [string, number][] {
  return (f.data as { name?: string; y?: number[] }[]).filter((t) => t.y?.length).map((t) => {
    const y = [...(t.y as number[])].sort((p, q) => p - q);
    const mid = y.length % 2 ? y[(y.length - 1) / 2] : (y[y.length / 2 - 1] + y[y.length / 2]) / 2;
    return [t.name ?? "", mid] as [string, number];
  }).sort((p, q) => p[1] - q[1]);
}
const relCount = (f: FigJson, m: string) =>
  (f.data as { name?: string }[]).map((t) => new RegExp(`^${m} breach \\((\\d+)\\)`).exec(t.name ?? "")).find(Boolean)?.[1] ?? "?";
// Share of stock-days within +/-2% in the Figure 2 histograms (bin centres are in %).
function shareSmall(f: FigJson) {
  let small = 0, all = 0;
  for (const t of f.data as { x?: number[]; y?: number[] }[]) {
    (t.y || []).forEach((c, i) => { all += c; if (Math.abs((t.x as number[])[i]) < 2) small += c; });
  }
  return all ? `${Math.round((100 * small) / all)}%` : "most";
}

interface Daily { ticker: string; dates: string[]; ret: number[]; var: Record<string, number[]>; es: Record<string, number[]> }
interface StockInfo { ticker: string; name: string; sector: string }
type Range = "1M" | "3M" | "6M" | "1Y" | "All" | "hike";
const file = (t: string) => `daily/${t.replace("&", "_and_")}.json`;
const mean = (v: number[]) => (v.length ? v.reduce((a, b) => a + b, 0) / v.length : NaN);

// Average 95% and 99% VaR over the test window for every stock and one model, from the per-stock daily files.
function useAllDaily(tickers: string[]) {
  const [state, setState] = useState<Record<string, Daily>>({});
  useEffect(() => {
    let alive = true;
    (async () => {
      const out: Record<string, Daily> = {};
      for (let i = 0; i < tickers.length; i += 6) {
        const part = await Promise.all(tickers.slice(i, i + 6).map((t) => fetchJson<Daily>(file(t)).catch(() => null)));
        part.forEach((d, j) => { if (d) out[tickers[i + j]] = d; });
        if (!alive) return;
        setState({ ...out });
      }
    })();
    return () => { alive = false; };
  }, [tickers.join(",")]);
  return state;
}

export default function Stock() {
  const stocks = useJson<StockInfo[]>("stocks.json");
  const backtest = useJson<Record<string, BacktestRow[]>>("backtest.json");
  const meta = useJson<Meta>("meta.json");
  const { ticker, setTicker, query } = useStore();
  const [mA, setMA] = useState("GJR-t");
  const [mB, setMB] = useState("XGBoost");
  const [level, setLevel] = useState<"99" | "95">("99");
  const [range, setRange] = useState<Range>("All");
  const [sector, setSector] = useState("all");
  const daily = useJson<Daily>(file(ticker));
  const allDaily = useAllDaily(useMemo(() => (stocks.data || []).map((s) => s.ticker), [stocks.data]));
  const phone = isPhone();

  const hike = meta.data?.hike_date;
  const xr = useMemo(() => {
    const d = daily.data;
    if (!d) return null;
    const last = d.dates[d.dates.length - 1];
    if (range === "All") return [d.dates[0], last];
    if (range === "hike") return hike ? [hike, last] : null;
    const months = { "1M": 1, "3M": 3, "6M": 6, "1Y": 12 }[range];
    const s = new Date(last); s.setMonth(s.getMonth() - months);
    return [s.toISOString().slice(0, 10), last];
  }, [daily.data, range, hike]);

  const traces = useMemo(() => {
    const d = daily.data;
    if (!d) return [];
    const out: Plotly.Data[] = [
      { x: d.dates, y: d.ret.map((v) => 100 * v), type: "scatter", mode: "lines", name: "Real daily return", line: { color: "#6b7280", width: 1 } },
    ];
    const models = [mB, mA].filter((m, i, a) => a.indexOf(m) === i); // first-chosen model drawn last (on top)
    for (const m of models) {
      const v = d.var[`${m}|${level}`] || [];
      out.push({ x: d.dates, y: v.map((x) => -100 * x), type: "scatter", mode: "lines", name: `${m} likely worst daily loss`, line: { color: COLOURS[m], width: 1.8 } });
    }
    for (const m of models) {
      const v = d.var[`${m}|${level}`] || [];
      const idx = d.ret.map((r, i) => (r < -v[i] ? i : -1)).filter((i) => i >= 0);
      out.push({
        x: idx.map((i) => d.dates[i]), y: idx.map((i) => 100 * d.ret[i]), type: "scatter", mode: "markers",
        name: `${m}: loss bigger than forecast (${idx.length} days)`,
        marker: GARCH.includes(m)
          ? { symbol: "triangle-down", size: 11, color: COLOURS[m], line: { width: 1, color: "white" } }
          : { symbol: "x-thin-open", size: 13, color: COLOURS[m], line: { width: 2.5, color: COLOURS[m] } },
      });
    }
    return out;
  }, [daily.data, mA, mB, level]);

  // y range fitted to the visible dates
  const yr = useMemo(() => {
    const d = daily.data;
    if (!d || !xr) return undefined;
    const vals: number[] = [];
    d.dates.forEach((t, i) => {
      if (t < xr[0] || t > xr[1]) return;
      vals.push(100 * d.ret[i]);
      for (const m of [mA, mB]) { const v = d.var[`${m}|${level}`]; if (v) vals.push(-100 * v[i]); }
    });
    if (!vals.length) return undefined;
    const lo = Math.min(...vals), hi = Math.max(...vals), pad = 0.08 * (hi - lo || 1);
    return [lo - pad, hi + pad];
  }, [daily.data, xr, mA, mB, level]);

  const bt = backtest.data?.price || [];
  const rows = bt.filter((r) => r.ticker === ticker);
  const modelOpts = ORDER.map((m) => ({ value: m, label: `${m} (${GARCH.includes(m) ? "classic" : ML.includes(m) ? "machine learning" : "benchmark"})` }));
  const info = stocks.data?.find((s) => s.ticker === ticker);
  const a = level === "99" ? 0.01 : 0.05;
  const picked = [mA, mB].filter((m, i, arr) => arr.indexOf(m) === i)
    .map((m) => rows.find((r) => r.model === m && Math.abs(r.alpha - a) < 1e-9)).filter(Boolean) as BacktestRow[];
  const ideal = picked[0] ? (picked[0].n * a).toFixed(0) : "";
  const name = info?.name ?? ticker;
  const q = query.trim().toUpperCase();
  const stockOpts = (stocks.data || []).filter((s) => !q || s.ticker === ticker || s.ticker.toUpperCase().includes(q) || s.name.toUpperCase().includes(q))
    .map((s) => ({ value: s.ticker, label: `${s.ticker.replace(".NS", "")} (${s.sector})` }));

  // right rail: stocks with the most 99% breaches for the first model
  const watch = bt.filter((r) => r.model === mA && Math.abs(r.alpha - 0.01) < 1e-9).sort((x, y) => y.exceptions - x.exceptions).slice(0, 6);
  // table
  const sectors = [...new Set((stocks.data || []).map((s) => s.sector))].sort();
  const br99 = (t: string) => bt.find((r) => r.ticker === t && r.model === mA && Math.abs(r.alpha - 0.01) < 1e-9);
  const tableRows = (stocks.data || []).filter((s) => sector === "all" || s.sector === sector).filter((s) => allDaily[s.ticker] && br99(s.ticker))
    .map((s) => ({ s, v95: mean(allDaily[s.ticker].var[`${mA}|95`] || []), v99: mean(allDaily[s.ticker].var[`${mA}|99`] || []), br: br99(s.ticker)!.exc_rate }))
    .sort((x, y) => y.v99 - x.v99);
  const loadedAll = stocks.data && Object.keys(allDaily).length === stocks.data.length;

  return (
    <>
      <Takeaway>
        {picked.length
          ? `${picked.map((r) => `${r.model} was beaten on ${r.exceptions} days.`).join(" ")} About ${ideal} would be ideal.`
          : `Choose a stock and two models to compare.`}
      </Takeaway>

      <div className="mb-10 grid gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
        <section className="card min-w-0 p-4 sm:p-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3">
              <StockBadge ticker={ticker} />
              <div className="min-w-0">
                <h2 className="text-lg font-semibold text-navy-900">{name}: forecast against real loss</h2>
                {info && <div className="text-[13px] text-slate-500">{ticker.replace(".NS", "")} · {info.sector}</div>}
              </div>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 gap-3 xs:grid-cols-2 lg:grid-cols-4">
            {stocks.data && <Select label="Stock" value={ticker} onChange={setTicker} options={stockOpts} />}
            <Select label="First model" value={mA} onChange={setMA} options={modelOpts} />
            <Select label="Second model" value={mB} onChange={setMB} options={modelOpts} />
            <Select<"99" | "95"> label="Likely worst daily loss: which level?" value={level} onChange={setLevel}
              options={[{ value: "99", label: "99 out of 100 days" }, { value: "95", label: "19 out of 20 days" }]} />
          </div>
          <div className="mt-4">
            <Pills<Range> label="Time range" value={range} onChange={setRange}
              options={[{ value: "1M", label: "1M" }, { value: "3M", label: "3M" }, { value: "6M", label: "6M" }, { value: "1Y", label: "1Y" },
                { value: "All", label: "All" }, ...(hike ? [{ value: "hike" as Range, label: "Since 7 Oct 2026 hike" }] : [])]} />
          </div>
          <div className="mt-4">
            <HowToRead>
              The grey line is the real daily return. Each coloured line is a model's likely worst daily loss ({LEVEL_TEXT[level]}). A mark below
              a line is a day the real loss was bigger than that model's forecast. The dashed amber line is the RBI rate rise of 7 October 2026.
            </HowToRead>
          </div>
          {picked[0] && (
            <div className="mt-3" data-read>
              <div className="kpi text-navy-900">{picked[0].exceptions}<span className="ml-2 text-lg font-semibold tracking-normal text-slate-500">beaten days</span></div>
              <p className="mt-1 text-[13px] text-slate-500">{picked[0].model}, whole test period. About {ideal} would be ideal.</p>
            </div>
          )}
          {daily.loading && <Loading what="daily forecasts" />}
          {daily.error && <ErrorBox error={daily.error} />}
          {daily.data && (
            <div className="mt-2">
              <Plot data={traces} style={{ height: phone ? 440 : 500 }}
                layout={chartFont({
                  autosize: true, height: phone ? 440 : 500, paper_bgcolor: "white", plot_bgcolor: "white",
                  xaxis: { title: { text: "Date" }, range: xr ?? undefined, gridcolor: "#eef0f3" },
                  yaxis: { title: { text: "Daily return (%)" }, range: yr, gridcolor: "#eef0f3", zerolinecolor: "#d1d5db" },
                  legend: { orientation: "h", y: phone ? -0.32 : -0.2 }, margin: { t: 10, l: phone ? 50 : 60, r: 15, b: phone ? 120 : 80 },
                  shapes: hike ? [{ type: "line", x0: hike, x1: hike, yref: "paper", y0: 0, y1: 1, line: { color: "#d18f00", dash: "dash", width: 2 } }] : [],
                })} />
            </div>
          )}
          {picked.length > 0 && (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {picked.map((r) => (
                <div key={r.model} className="rounded-lg border border-line p-3" data-read>
                  <ModelName m={r.model} />
                  <p className="mt-1">Beaten on {r.exceptions} of {r.n} days. About {ideal} would be ideal.</p>
                  <p className="mt-1 flex flex-wrap items-center gap-2">
                    Did forecasts fail too often? <Status level={r.kupiec_p > 0.05 ? "good" : "poor"} />
                    <span className="text-sm">{r.kupiec_p > 0.05 ? "No" : "Yes, or far too rarely"}</span>
                  </p>
                </div>
              ))}
            </div>
          )}
          <Means>
            One stock has only about {picked[0] ? Math.round(picked[0].n * a) : "a few"} expected bad days in the test period, so chance plays a big part.
            Use the results across all stocks for decisions; use this view to see how each model behaves.
          </Means>
        </section>

        {watch.length > 0 && (
          <aside className="card h-fit p-5">
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-semibold text-navy-900">Stocks to watch</h2>
            </div>
            <p className="mt-1 text-[13px] text-slate-500">Most days beaten by {mA} (99 out of 100 days)</p>
            <ul className="mt-3 divide-y divide-line">
              {watch.map((r) => (
                <li key={r.ticker}>
                  <button onClick={() => { setTicker(r.ticker); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                    className="flex w-full items-center gap-3 py-2.5 text-left hover:bg-slate-50">
                    <StockBadge ticker={r.ticker} />
                    <span className="min-w-0 flex-1">
                      <span className="block font-semibold text-navy-900">{r.ticker.replace(".NS", "")}</span>
                      <span className="block truncate text-[13px] text-slate-500">{stocks.data?.find((s) => s.ticker === r.ticker)?.sector}</span>
                    </span>
                    <span className="text-right">
                      <span className="block font-semibold text-navy-900">{r.exceptions} days</span>
                      <span className="block text-[13px] text-slate-500">{pct(r.exc_rate)}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>

      <Experts title="backtest results for this stock (all models)">
        {rows.length === 0 ? <Empty>No backtest rows for this stock.</Empty> : (
          <Table
            head={["Model", "Level", "Breaches", "Breach rate", "Kupiec p", "Christoffersen CC p", "Basel Green", "FZ0", "Actual/forecast ES"]}
            rows={ORDER.flatMap((m) => [0.05, 0.01].map((a) => rows.find((r) => r.model === m && Math.abs(r.alpha - a) < 1e-9)!))
              .filter(Boolean)
              .map((r) => [r.model, r.alpha === 0.01 ? "99%" : "95%", r.exceptions, pct(r.exc_rate), num(r.kupiec_p, 3), num(r.cc_p, 3),
                r.alpha === 0.01 ? pct(r.basel_green_share, 0) : "–", num(r.fz0), num(r.actual_over_expected_es, 3)])}
          />
        )}
      </Experts>

      <Section title="All stocks">
        <div className="card p-4 sm:p-6">
          <p className="mb-3 text-[15px] text-slate-700" data-read>
            Average likely worst daily loss from {mA} over the test period, and how often it was beaten. Click a row to see that stock.
          </p>
          <Pills label="Sector" value={sector} onChange={setSector}
            options={[{ value: "all", label: "All sectors" }, ...sectors.map((s) => ({ value: s, label: s }))]} />
          {!loadedAll && <div className="mt-4"><Loading what="stock table" /></div>}
          {loadedAll && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-[13px] text-slate-500">
                  <tr>
                    <th className="font-medium">Stock</th>
                    <th className="font-medium ph:hidden">Sector</th>
                    <th className="text-right font-medium ph:hidden">Worst loss, 19 of 20 days</th>
                    <th className="text-right font-medium">Worst loss, 99 of 100 days</th>
                    <th className="text-right font-medium">Share of days beaten (99 of 100)</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map(({ s, v95, v99, br }, i) => (
                    <tr key={s.ticker} onClick={() => { setTicker(s.ticker); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                      className={`cursor-pointer border-t border-line hover:bg-slate-100 ${i % 2 ? "bg-slate-50" : ""} ${s.ticker === ticker ? "font-semibold" : ""}`}>
                      <td>
                        <span className="flex items-center gap-2">
                          <StockBadge ticker={s.ticker} />
                          <span><span className="block text-navy-900">{s.ticker.replace(".NS", "")}</span>
                            <span className="block text-[13px] font-normal text-slate-500 ph:hidden">{s.name}</span></span>
                        </span>
                      </td>
                      <td className="ph:hidden">{s.sector}</td>
                      <td className="text-right ph:hidden">{pct(v95)}</td>
                      <td className="text-right">{pct(v99)}</td>
                      <td className="text-right">{pct(br)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Section>

      <Section title="All stocks and sectors">
        <Figure name="fig09_sector_var" number="Figure 9"
          title={(f) => { const s = sectorMedians(f); return s.length ? `${s[s.length - 1][0]} stocks had the biggest likely worst daily loss; ${s[0][0]} the smallest` : "Likely worst daily loss by sector"; }}
          how="Each dot is one stock. It shows the stock's average likely worst daily loss from GJR-t. Boxes group stocks by sector."
          means={(f) => { const s = sectorMedians(f); return s.length ? `A typical ${s[s.length - 1][0]} stock needed about ${s[s.length - 1][1].toFixed(1)}% of the position set aside for a bad day, against about ${s[0][1].toFixed(1)}% for ${s[0][0]}. Margins and limits should differ by sector.` : ""; }}
          patch={() => ({ yaxis: { title: { text: phone ? "Worst daily loss (% of position)" : "Likely worst daily loss, 99 out of 100 days (% of position)" } } })} />
        <Figure name="fig02_return_distributions" number="Figure 2"
          title={(f) => `On ${shareSmall(f)} of stock-days the price moved less than 2% either way; big moves were rare`}
          how="Each small chart is one stock. Bars count test days by the size of the daily move, from −8% (left) to +8% (right)."
          means="Most days are quiet. The rare big moves in the tails are what the risk models must catch." />
        <Figure name="fig03_var_vs_returns_RELIANCE" number="Figure 3"
          title={(f) => `Reliance: GJR-t was beaten on ${relCount(f, "GJR-t")} days and XGBoost on ${relCount(f, "XGBoost")} (99 out of 100 days)`}
          how="The same view as the chart above, fixed on Reliance Industries, the example used in the report."
          means={(f) => {
            const g = Number(relCount(f, "GJR-t")), x = Number(relCount(f, "XGBoost"));
            const n = ((f.data[0] as { x?: unknown[] }).x || []).length;
            return `About ${Math.round(n / 100)} beaten days would be ideal over these ${n} days. ${x > g ? "XGBoost was beaten more often than GJR-t on this stock." : x < g ? "GJR-t was beaten more often than XGBoost on this stock." : "Both were beaten equally often."}`;
          }} />
      </Section>
    </>
  );
}
