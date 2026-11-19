import { useState } from "react";
import { Empty, ErrorBox, Loading, Section, Table } from "../components/ui";
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
  if (!live.data?.length) return <Empty>No live risk file yet. It is written by the daily GitHub Action.</Empty>;
  const rows = [...live.data].sort((a, b) =>
    sort === "ticker" || sort === "sector" ? a[sort].localeCompare(b[sort]) : (b[sort] as number) - (a[sort] as number));
  const vix = live.data[0].india_vix_change_1d;
  return (
    <Section title="Latest one-day risk (live extension)"
      note={<>
        <b>This is the live extension, not the report results.</b> Updated each weekday evening by a GitHub Action from Yahoo
        Finance; report numbers come only from the frozen snapshot. Model: GJR-GARCH(1,1) with Student-t errors on the last
        1,500 daily returns. VaR and ES are positive loss numbers for the next trading day (2.50% = a loss of 2.5% of the position).
      </>}>
      <p className="mb-3 text-sm text-slate-700">
        As of {live.data[0].as_of} · generated {live.data[0].generated_utc} UTC
        {meta.data?.live_generated_utc ? "" : ""} · India VIX one-day change: {vix == null ? "n/a" : pct(vix, 1)}
      </p>
      <div className="mb-3 flex flex-wrap gap-2 text-sm">
        Sort by:
        {(["var_99", "es_99", "var_95", "sector", "ticker"] as Key[]).map((k) => (
          <button key={k} onClick={() => setSort(k)}
            className={`rounded border px-2 py-0.5 ${sort === k ? "border-slate-800 bg-slate-800 text-white" : "border-slate-300"}`}>
            {k.replace("_", " ")}
          </button>
        ))}
      </div>
      <Table
        head={["Stock", "Sector", "Last return", "1-day volatility", "Tail index (nu)", "VaR 95%", "ES 95%", "VaR 99%", "ES 99%"]}
        rows={rows.map((r) => [r.ticker.replace(".NS", ""), r.sector, pct(r.last_return), pct(r.sigma_1d), num(r.nu, 2),
          pct(r.var_95), pct(r.es_95), pct(r.var_99), pct(r.es_99)])}
      />
    </Section>
  );
}
