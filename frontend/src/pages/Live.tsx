import { useState } from "react";
import { Empty, ErrorBox, Loading, Section, Table } from "../components/ui";
import { Experts, HowToRead, Means, Takeaway } from "../components/plain";
import { num, pct, useJson, type Meta } from "../lib/data";

interface LiveRow {
  as_of: string; ticker: string; sector: string; last_return: number; sigma_1d: number; nu: number;
  var_95: number; es_95: number; var_99: number; es_99: number; india_vix_change_1d: number | null; generated_utc: string;
}
type Key = "var_99" | "es_99" | "var_95" | "ticker" | "sector";

export default function Live() {
  const live = useJson<LiveRow[]>("live_risk.json");
  const meta = useJson<Meta>("meta.json");
  const [sort, setSort] = useState<Key>("var_99");
  if (live.loading) return <Loading what="live risk" />;
  if (live.error) return <ErrorBox error={live.error} />;
  if (!live.data?.length) return <Empty>No daily example yet. It is made each weekday evening.</Empty>;
  const rows = [...live.data].sort((a, b) =>
    sort === "ticker" || sort === "sector" ? a[sort].localeCompare(b[sort]) : (b[sort] as number) - (a[sort] as number));
  const vix = live.data[0].india_vix_change_1d;
  const top = [...live.data].sort((a, b) => b.var_99 - a.var_99)[0];
  const low = [...live.data].sort((a, b) => a.var_99 - b.var_99)[0];
  const LABELS: Record<Key, string> = { var_99: "Worst loss (99 of 100 days)", es_99: "Very bad days (99 of 100)", var_95: "Worst loss (19 of 20 days)", sector: "Sector", ticker: "Stock" };
  return (
    <>
      <div className="mb-4 rounded-lg border-2 border-warn-500 bg-warn-100 p-3 text-lg font-semibold text-warn-700" data-read>
        Daily example only. This is not the report's results. It updates each weekday evening.
      </div>
      <Takeaway>
        In today's example, {top.ticker.replace(".NS", "")} has the biggest likely loss for the next trading day.{" "}
        {low.ticker.replace(".NS", "")} has the smallest.
      </Takeaway>
      <Section title="Daily example: next day's likely worst loss for each stock">
        <HowToRead>
          Each row is one stock. “Worst loss (99 of 100 days)” is the loss the stock should not pass on 99 out of 100 days.
          2.50% means a loss of ₹2.50 on every ₹100 held. “Very bad days” is the average loss if that line is passed.
        </HowToRead>
        <p className="mb-3 text-sm text-slate-700">
          Prices up to {live.data[0].as_of} · made {live.data[0].generated_utc} UTC · Market fear gauge (India VIX) change on the last day:{" "}
          {vix == null ? "not available" : pct(vix, 1)}
        </p>
        <div className="mb-3 flex flex-wrap gap-2 text-sm">
          Sort by:
          {(["var_99", "es_99", "var_95", "sector", "ticker"] as Key[]).map((k) => (
            <button key={k} onClick={() => setSort(k)}
              className={`rounded border px-2 py-0.5 ${sort === k ? "border-slate-800 bg-slate-800 text-white" : "border-slate-300"}`}>
              {LABELS[k]}
            </button>
          ))}
        </div>
        <Table
          head={["Stock", "Sector", "Worst loss (99 of 100 days)", "Very bad days (99 of 100)", "Worst loss (19 of 20 days)"]}
          rows={rows.map((r) => [r.ticker.replace(".NS", ""), r.sector, pct(r.var_99), pct(r.es_99), pct(r.var_95)])}
        />
        <Means>
          A broker or fund could use a list like this each evening to set how much cash to hold against each stock. It comes from one
          classic model (GJR-t), the type that stayed closest to expected in the study.
        </Means>
      </Section>
      <Experts title="full live table and model details">
        <p className="mb-2 text-sm text-slate-600">
          Live extension, not the report results. Updated each weekday evening by a GitHub Action from Yahoo Finance; report numbers
          come only from the frozen snapshot. Model: GJR-GARCH(1,1) with Student-t errors on the last 1,500 daily returns. VaR and ES
          are positive loss numbers for the next trading day.
          {meta.data?.live_generated_utc ? ` Exported ${meta.data.live_generated_utc} UTC.` : ""}
        </p>
        <Table
          head={["Stock", "Sector", "Last return", "1-day volatility", "Tail index (nu)", "VaR 95%", "ES 95%", "VaR 99%", "ES 99%"]}
          rows={rows.map((r) => [r.ticker.replace(".NS", ""), r.sector, pct(r.last_return), pct(r.sigma_1d), num(r.nu, 2),
            pct(r.var_95), pct(r.es_95), pct(r.var_99), pct(r.es_99)])}
        />
      </Experts>
    </>
  );
}
