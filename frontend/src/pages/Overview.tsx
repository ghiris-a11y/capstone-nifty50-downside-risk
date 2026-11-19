import { useState } from "react";
import { Card, ErrorBox, Loading, Section, Select, Table } from "../components/ui";
import { Experts, Takeaway, Tech } from "../components/plain";
import BeatenChart from "../components/BeatenChart";
import { family, GARCH, ML, num, ORDER, pct, per100, useJson, type BacktestRow, type DmCount, type SummaryFile } from "../lib/data";

type Fam = "all" | "GARCH" | "ML" | "Benchmark";
type Level = "0.01" | "0.05";

export default function Overview() {
  const s = useJson<SummaryFile>("summary.json");
  const dm = useJson<Record<string, Record<string, DmCount[]>>>("dm.json");
  const breach = useJson<Record<string, { model: string; alpha: number; share_of_breaches_on_stress_days: number; share_of_days_stress: number }[]>>("breach_summary.json");
  const bt = useJson<Record<string, BacktestRow[]>>("backtest.json");
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
  const lv = level === "0.01" ? "99" : "95";
  const worstNoRisk = (bt.data?.[set] || []).filter((r) => r.model === "XGBoost" && Math.abs(r.alpha - 0.01) < 1e-9 && r.norisk_days > 0)
    .sort((x, y) => y.fz0 - x.fz0)[0];
  const garchClosest = closest.slice(0, 3).every((m) => GARCH.includes(m));
  return (
    <>
      <Takeaway>
        {garchClosest
          ? "The GARCH models stayed closest to the loss limits we expected. The machine-learning models were beaten more often."
          : "The models closest to the expected loss limits came from more than one family."}
      </Takeaway>
      <div className="mb-6 flex flex-wrap gap-4">
        <Select label="Inputs used by the machine-learning models" value={set} onChange={setSet}
          options={Object.entries(s.data.labels).map(([value, label]) => ({ value, label }))} />
        <Select<Level> label="Likely worst daily loss: which level?" value={level} onChange={setLevel}
          options={[{ value: "0.01", label: "99 out of 100 days" }, { value: "0.05", label: "19 out of 20 days" }]} />
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3" data-read>
        <Card title="Closest to expected (99 out of 100 days)" tone="garch">
          {closest.slice(0, 3).map((m) => `${m}: ${per100(at(m, 0.01).exc_rate)}`).join(" · ")} days in 100. The ideal is 1.
          <Tech>99% VaR breach rate closest to nominal 1%</Tech>
        </Card>
        <Card title="Is the difference real, or just luck?" tone="ml">
          GARCH was really better in {tot.g} comparisons. Machine learning was really better in {tot.m}. The other {tot.n} could be luck.
          <Tech k="dm">Diebold-Mariano test on FZ0 at 95%, 5% level, each ML model vs each GARCH model, per stock</Tech>
        </Card>
        <Card title="Regulator-style safety check (green = pass)">
          GJR-t passed for {pct(at("GJR-t", 0.01).green99, 0)} of stocks. XGBoost passed for {pct(at("XGBoost", 0.01).green99, 0)}.
          <Tech>Basel traffic-light Green share, 99% VaR only</Tech>
        </Card>
        <Card title="XGBoost sometimes saw no risk" tone="warn">
          On {at("XGBoost", 0.01).norisk_days} stock-days it forecast no loss at all (99 out of 100 level).
          {worstNoRisk && <> One such day for {worstNoRisk.ticker.replace(".NS", "")} made that stock's average score very poor.</>}
          <Tech>No-risk days: forecast quantile at or above zero</Tech>
        </Card>
        {gjr && (
          <Card title="Bad days come together" tone="warn">
            Market-wide bad days were {pct(gjr.share_of_days_stress, 1)} of days. They held {pct(gjr.share_of_breaches_on_stress_days, 1)} of
            the days GJR-t was beaten.
            <Tech>Share of 99% breaches on stress days (Nifty 50 fell 2% or more)</Tech>
          </Card>
        )}
      </div>

      <BeatenChart rows={rows} level={lv} />

      <Experts title="full backtest summary table">
        <div className="mb-3">
          <Select<Fam> label="Model family" value={fam} onChange={setFam}
            options={[{ value: "all", label: "All" }, { value: "GARCH", label: "GARCH" }, { value: "ML", label: "Machine learning" }, { value: "Benchmark", label: "Benchmark" }]} />
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
      </Experts>
    </>
  );
}
