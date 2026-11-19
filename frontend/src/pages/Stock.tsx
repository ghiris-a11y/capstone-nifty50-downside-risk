import { useMemo, useState } from "react";
import Figure from "../components/Figure";
import Plot from "../components/Plot";
import { Empty, ErrorBox, Loading, Section, Select, Table } from "../components/ui";
import { COLOURS, GARCH, num, ORDER, pct, useJson, type BacktestRow, type Meta } from "../lib/data";

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
      { x: d.dates, y: d.ret.map((v) => 100 * v), type: "scatter", mode: "lines", name: "Actual daily return", line: { color: "#4d4d4d", width: 1 } },
    ];
    const models = [mB, mA].filter((m, i, a) => a.indexOf(m) === i); // first-chosen model drawn last (on top)
    for (const m of models) {
      const v = d.var[`${m}|${level}`] || [];
      out.push({ x: d.dates, y: v.map((x) => -100 * x), type: "scatter", mode: "lines", name: `${m} ${level}% VaR (as return)`, line: { color: COLOURS[m], width: 1.8 } });
    }
    for (const m of models) {
      const v = d.var[`${m}|${level}`] || [];
      const idx = d.ret.map((r, i) => (r < -v[i] ? i : -1)).filter((i) => i >= 0);
      out.push({
        x: idx.map((i) => d.dates[i]), y: idx.map((i) => 100 * d.ret[i]), type: "scatter", mode: "markers",
        name: `${m} breach (${idx.length})`,
        marker: GARCH.includes(m)
          ? { symbol: "triangle-down", size: 11, color: COLOURS[m], line: { width: 1, color: "white" } }
          : { symbol: "x-thin-open", size: 13, color: COLOURS[m], line: { width: 2.5, color: COLOURS[m] } },
      });
    }
    return out;
  }, [daily.data, mA, mB, level]);

  const rows = (backtest.data?.price || []).filter((r) => r.ticker === ticker);
  const modelOpts = ORDER.map((m) => ({ value: m, label: m }));
  const info = stocks.data?.find((s) => s.ticker === ticker);
  return (
    <>
      <div className="mb-4 flex flex-wrap gap-4">
        {stocks.data && (
          <Select label="Stock" value={ticker} onChange={setTicker}
            options={stocks.data.map((s) => ({ value: s.ticker, label: `${s.ticker.replace(".NS", "")} (${s.sector})` }))} />
        )}
        <Select label="Model A" value={mA} onChange={setMA} options={modelOpts} />
        <Select label="Model B" value={mB} onChange={setMB} options={modelOpts} />
        <Select<"99" | "95"> label="VaR level" value={level} onChange={setLevel} options={[{ value: "99", label: "99%" }, { value: "95", label: "95%" }]} />
      </div>
      <Section title={`${info?.name ?? ticker}: VaR forecast against actual returns`}
        note="Each marker is a breach: a day on which the loss was larger than that model's VaR forecast. ML models use the price/volume feature set.">
        {daily.loading && <Loading what="daily forecasts" />}
        {daily.error && <ErrorBox error={daily.error} />}
        {daily.data && (
          <div className="rounded-lg border border-slate-200 p-2">
            <Plot data={traces} style={{ height: 520 }}
              layout={{
                autosize: true, height: 520, template: undefined, font: { family: "Times New Roman, serif", size: 14 },
                xaxis: { title: { text: "Date" } }, yaxis: { title: { text: "Daily log return (%)" } },
                legend: { orientation: "h", y: -0.2 }, margin: { t: 20, l: 60, r: 20, b: 80 },
                shapes: meta.data ? [{ type: "line", x0: meta.data.hike_date, x1: meta.data.hike_date, yref: "paper", y0: 0, y1: 1, line: { color: "#d18f00", dash: "dash", width: 2 } }] : [],
              }} />
          </div>
        )}
      </Section>
      <Section title="Backtest results for this stock">
        {rows.length === 0 ? <Empty>No backtest rows for this stock.</Empty> : (
          <Table
            head={["Model", "Level", "Breaches", "Breach rate", "Kupiec p", "Christoffersen CC p", "Basel Green", "FZ0", "Actual/forecast ES"]}
            rows={ORDER.flatMap((m) => [0.05, 0.01].map((a) => rows.find((r) => r.model === m && Math.abs(r.alpha - a) < 1e-9)!))
              .filter(Boolean)
              .map((r) => [r.model, r.alpha === 0.01 ? "99%" : "95%", r.exceptions, pct(r.exc_rate), num(r.kupiec_p, 3), num(r.cc_p, 3),
                r.alpha === 0.01 ? pct(r.basel_green_share, 0) : "–", num(r.fz0), num(r.actual_over_expected_es, 3)])}
          />
        )}
      </Section>
      <Section title="All stocks and sectors">
        <Figure name="fig03_var_vs_returns_RELIANCE" number="Figure 3" />
        <Figure name="fig09_sector_var" number="Figure 9" />
        <Figure name="fig02_return_distributions" number="Figure 2" />
      </Section>
    </>
  );
}
