import { useState } from "react";
import { Card, ErrorBox, Loading, Section, Select, Table } from "../components/ui";
import { family, GARCH, ML, num, ORDER, pct, useJson, type DmCount, type SummaryFile } from "../lib/data";

type Fam = "all" | "GARCH" | "ML" | "Benchmark";
type Level = "0.01" | "0.05";

export default function Overview() {
  const s = useJson<SummaryFile>("summary.json");
  const dm = useJson<Record<string, Record<string, DmCount[]>>>("dm.json");
  const breach = useJson<Record<string, { model: string; alpha: number; share_of_breaches_on_stress_days: number; share_of_days_stress: number }[]>>("breach_summary.json");
  const [set, setSet] = useState("price");
  const [fam, setFam] = useState<Fam>("all");
  const [level, setLevel] = useState<Level>("0.01");

  if (s.loading) return <Loading />;
  if (s.error || !s.data) return <ErrorBox error={s.error || "no summary"} />;
  const rows = s.data.summary[set];
  const at = (m: string, a: number) => rows.find((r) => r.model === m && Math.abs(r.alpha - a) < 1e-9)!;
  const closest = [...ORDER].sort((a, b) => Math.abs(at(a, 0.01).exc_rate - 0.01) - Math.abs(at(b, 0.01).exc_rate - 0.01));
  const lowestMedianFz = [...ORDER].sort((a, b) => at(a, 0.05).fz0_median_stocks - at(b, 0.05).fz0_median_stocks)[0];
  const bestGarchKupiec = [...GARCH].sort((a, b) => at(b, 0.01).pass_kupiec - at(a, 0.01).pass_kupiec)[0];
  const bestMlKupiec = [...ML].sort((a, b) => at(b, 0.01).pass_kupiec - at(a, 0.01).pass_kupiec)[0];
  const tot = (dm.data?.[set]?.fz0_95 || []).reduce((t, r) => ({ g: t.g + r.garch, m: t.m + r.ml, n: t.n + r.none }), { g: 0, m: 0, n: 0 });
  const bs = breach.data?.[set]?.filter((r) => r.alpha === 0.01) || [];
  const gjr = bs.find((r) => r.model === "GJR-t");

  const a = Number(level);
  const shown = ORDER.filter((m) => fam === "all" || family(m) === fam);
  return (
    <>
      <div className="mb-6 flex flex-wrap gap-4">
        <Select label="Feature set for the ML models" value={set} onChange={setSet}
          options={Object.entries(s.data.labels).map(([value, label]) => ({ value, label }))} />
        <Select<Fam> label="Model family" value={fam} onChange={setFam}
          options={[{ value: "all", label: "All" }, { value: "GARCH", label: "GARCH" }, { value: "ML", label: "Machine learning" }, { value: "Benchmark", label: "Benchmark" }]} />
        <Select<Level> label="VaR level" value={level} onChange={setLevel}
          options={[{ value: "0.01", label: "99%" }, { value: "0.05", label: "95%" }]} />
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card title="Closest to nominal 1% (99% VaR)" tone="garch">
          {closest.slice(0, 3).map((m) => `${m} ${pct(at(m, 0.01).exc_rate)}`).join(", ")}
        </Card>
        <Card title="Lowest median joint VaR-ES loss (FZ0, 95%)">
          {lowestMedianFz} ({num(at(lowestMedianFz, 0.05).fz0_median_stocks)}); median across stocks, lower is better
        </Card>
        <Card title="Kupiec pass rate at 99% (share of stocks)">
          Best GARCH: {bestGarchKupiec} {pct(at(bestGarchKupiec, 0.01).pass_kupiec, 0)} · Best ML: {bestMlKupiec}{" "}
          {pct(at(bestMlKupiec, 0.01).pass_kupiec, 0)}
        </Card>
        <Card title="Basel Green share (99% only)">
          GJR-t {pct(at("GJR-t", 0.01).green99, 0)} · XGBoost {pct(at("XGBoost", 0.01).green99, 0)}. Read with Kupiec: the
          traffic light penalises too many breaches, not too few.
        </Card>
        <Card title="Diebold-Mariano (FZ0 95%, ML vs each GARCH model, per stock)" tone="ml">
          GARCH significantly better in {tot.g} pairs, ML in {tot.m}, no difference in {tot.n}
        </Card>
        <Card title="XGBoost no-risk days" tone="warn">
          {at("XGBoost", 0.05).norisk_days} at 95%, {at("XGBoost", 0.01).norisk_days} at 99% (forecast quantile at or above
          zero). Mean 99% FZ0 {num(at("XGBoost", 0.01).fz0)} vs median {num(at("XGBoost", 0.01).fz0_median_stocks)}.
        </Card>
        {gjr && (
          <Card title="Breaches on market-stress days (99%)" tone="warn">
            Stress days (Nifty ≤ −2%) are {pct(gjr.share_of_days_stress, 1)} of test days but carry{" "}
            {pct(gjr.share_of_breaches_on_stress_days, 1)} of GJR-t breaches.
          </Card>
        )}
      </div>

      <Section title={`Backtest summary, ${level === "0.01" ? "99%" : "95%"} VaR`}
        note="Averages across the stocks over the test window. Pass shares are the percentage of stocks with p > 0.05. Lower FZ0 and pinball are better; the median is shown because single days can dominate the mean.">
        <Table
          head={["Model", "Family", "Breach rate", "Nominal", "Kupiec pass", "Christoffersen CC pass", ...(a === 0.01 ? ["Basel Green"] : []),
            "Mean FZ0", "Median FZ0 (stocks)", "Pinball (×10⁴)", "Actual/forecast ES", "No-risk days"]}
          rows={shown.map((m) => {
            const r = at(m, a);
            return [m, family(m), pct(r.exc_rate), pct(a, 0), pct(r.pass_kupiec, 0), pct(r.pass_cc, 0),
              ...(a === 0.01 ? [pct(r.green99, 0)] : []), num(r.fz0), num(r.fz0_median_stocks), (1e4 * r.pinball).toFixed(2),
              num(r.es_ratio, 3), r.norisk_days];
          })}
          rowClass={(i) => (family(shown[i]) === "GARCH" ? "bg-garch-50" : family(shown[i]) === "ML" ? "bg-ml-50" : "")}
        />
      </Section>
    </>
  );
}
