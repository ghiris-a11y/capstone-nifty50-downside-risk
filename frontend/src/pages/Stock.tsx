import { useMemo, useState } from "react";
import Figure, { type FigJson } from "../components/Figure";
import Plot from "../components/Plot";
import { Empty, ErrorBox, Loading, Section, Select, Table } from "../components/ui";
import { Experts, HowToRead, Means, ModelName, Status, Takeaway } from "../components/plain";
import { COLOURS, GARCH, ML, num, ORDER, pct, useJson, type BacktestRow, type Meta } from "../lib/data";
import { LEVEL_TEXT } from "../lib/plain";

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

export default function Stock() {
  const stocks = useJson<StockInfo[]>("stocks.json");
  const backtest = useJson<Record<string, BacktestRow[]>>("backtest.json");
  const meta = useJson<Meta>("meta.json");
  const [ticker, setTicker] = useState("RELIANCE.NS");
  const [mA, setMA] = useState("GJR-t");
  const [mB, setMB] = useState("XGBoost");
  const [level, setLevel] = useState<"99" | "95">("99");
  const daily = useJson<Daily>(`daily/${ticker.replace("&", "_and_")}.json`);

  const traces = useMemo(() => {
    const d = daily.data;
    if (!d) return [];
    const out: Plotly.Data[] = [
      { x: d.dates, y: d.ret.map((v) => 100 * v), type: "scatter", mode: "lines", name: "Real daily return", line: { color: "#4d4d4d", width: 1 } },
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

  const rows = (backtest.data?.price || []).filter((r) => r.ticker === ticker);
  const modelOpts = ORDER.map((m) => ({ value: m, label: `${m} (${GARCH.includes(m) ? "classic" : ML.includes(m) ? "machine learning" : "benchmark"})` }));
  const info = stocks.data?.find((s) => s.ticker === ticker);
  const a = level === "99" ? 0.01 : 0.05;
  const picked = [mA, mB].filter((m, i, arr) => arr.indexOf(m) === i)
    .map((m) => rows.find((r) => r.model === m && Math.abs(r.alpha - a) < 1e-9)).filter(Boolean) as BacktestRow[];
  const ideal = picked[0] ? (picked[0].n * a).toFixed(0) : "";
  const name = info?.name ?? ticker;
  return (
    <>
      <Takeaway>
        {picked.length
          ? `${picked.map((r) => `${r.model} was beaten on ${r.exceptions} days.`).join(" ")} About ${ideal} would be ideal.`
          : `Choose a stock and two models to compare.`}
      </Takeaway>
      <div className="mb-4 flex flex-wrap gap-4">
        {stocks.data && (
          <Select label="Stock" value={ticker} onChange={setTicker}
            options={stocks.data.map((s) => ({ value: s.ticker, label: `${s.ticker.replace(".NS", "")} (${s.sector})` }))} />
        )}
        <Select label="First model" value={mA} onChange={setMA} options={modelOpts} />
        <Select label="Second model" value={mB} onChange={setMB} options={modelOpts} />
        <Select<"99" | "95"> label="Likely worst daily loss: which level?" value={level} onChange={setLevel}
          options={[{ value: "99", label: "99 out of 100 days" }, { value: "95", label: "19 out of 20 days" }]} />
      </div>
      <Section title={`${name}: forecast against real loss`}>
        <HowToRead>
          The grey line is the real daily return. Each coloured line is a model's likely worst daily loss ({LEVEL_TEXT[level]}). A mark below
          a line is a day the real loss was bigger than that model's forecast. The dashed amber line is the RBI rate rise of 7 October 2026.
        </HowToRead>
        {daily.loading && <Loading what="daily forecasts" />}
        {daily.error && <ErrorBox error={daily.error} />}
        {daily.data && (
          <div className="rounded-lg border border-slate-200 p-2">
            <Plot data={traces} style={{ height: 520 }}
              layout={{
                autosize: true, height: 520, template: undefined, font: { family: "Times New Roman, serif", size: 14 },
                xaxis: { title: { text: "Date" } }, yaxis: { title: { text: "Daily return (%)" } },
                legend: { orientation: "h", y: -0.2 }, margin: { t: 20, l: 60, r: 20, b: 80 },
                shapes: meta.data ? [{ type: "line", x0: meta.data.hike_date, x1: meta.data.hike_date, yref: "paper", y0: 0, y1: 1, line: { color: "#d18f00", dash: "dash", width: 2 } }] : [],
              }} />
          </div>
        )}
        {picked.length > 0 && (
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {picked.map((r) => (
              <div key={r.model} className="rounded border border-slate-200 p-3" data-read>
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
      </Section>
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
      <Section title="All stocks and sectors">
        <Figure name="fig09_sector_var" number="Figure 9"
          title={(f) => { const s = sectorMedians(f); return s.length ? `${s[s.length - 1][0]} stocks had the biggest likely worst daily loss; ${s[0][0]} the smallest` : "Likely worst daily loss by sector"; }}
          how="Each dot is one stock. It shows the stock's average likely worst daily loss from GJR-t. Boxes group stocks by sector."
          means={(f) => { const s = sectorMedians(f); return s.length ? `A typical ${s[s.length - 1][0]} stock needed about ${s[s.length - 1][1].toFixed(1)}% of the position set aside for a bad day, against about ${s[0][1].toFixed(1)}% for ${s[0][0]}. Margins and limits should differ by sector.` : ""; }}
          patch={() => ({ yaxis: { title: { text: "Likely worst daily loss, 99 out of 100 days (% of position)" } } })} />
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
