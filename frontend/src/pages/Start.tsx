import { Link } from "react-router-dom";
import { ErrorBox, Loading, Section } from "../components/ui";
import { Takeaway, Tech } from "../components/plain";
import { dmTotals, GARCH, ML, ORDER, per100, pct, rowAt, useJson, type BreachSummaryRow, type DmCount, type Meta, type SummaryFile } from "../lib/data";

export default function Start() {
  const s = useJson<SummaryFile>("summary.json");
  const dm = useJson<Record<string, Record<string, DmCount[]>>>("dm.json");
  const br = useJson<Record<string, BreachSummaryRow[]>>("breach_summary.json");
  const meta = useJson<Meta>("meta.json");
  if (s.loading || dm.loading || br.loading) return <Loading />;
  if (!s.data || !dm.data || !br.data) return <ErrorBox error={s.error || dm.error || br.error || "missing data"} />;

  const rows = s.data.summary.price;
  const r99 = (m: string) => rowAt(rows, m, 0.01).exc_rate;
  const closest = [...ORDER].sort((a, b) => Math.abs(r99(a) - 0.01) - Math.abs(r99(b) - 0.01)).slice(0, 3);
  const garchClosest = closest.every((m) => GARCH.includes(m));
  const tot = dmTotals(dm.data.price?.fz0_95);
  const mlAllAbove = ML.every((m) => r99(m) > 0.01);
  const gjr = br.data.price.find((r) => r.model === "GJR-t" && r.alpha === 0.01);

  return (
    <>
      <Takeaway>
        {garchClosest
          ? "The classic statistics models stayed closest to the loss limits we expected. The machine-learning models did not do better."
          : "No single family of models stayed closest to the loss limits we expected."}
      </Takeaway>

      <Section title="The question">
        <p className="max-w-3xl text-lg" data-read>
          How much could a big Indian stock lose tomorrow? We compared two ways to forecast that loss. One uses classic
          statistics. The other uses machine learning.
        </p>
      </Section>

      <Section title="Three key findings">
        <ol className="grid gap-4 md:grid-cols-3">
          <li className="rounded-lg border border-garch-100 bg-garch-50 p-4" data-read>
            <div className="text-sm font-semibold text-garch-700">1 · Closest to expected</div>
            <p className="mt-1 text-lg">
              {closest.map((m) => `${m} (${per100(r99(m))})`).join(", ")} came closest to the ideal of 1 bad day in 100.
              {garchClosest && " All three are classic models that allow for extreme days."}
            </p>
            <Tech>99% VaR breach rate closest to nominal 1%</Tech>
          </li>
          <li className="rounded-lg border border-ml-100 bg-ml-50 p-4" data-read>
            <div className="text-sm font-semibold text-ml-700">2 · Machine learning did not do better</div>
            <p className="mt-1 text-lg">
              {mlAllAbove ? "The machine-learning models were beaten more often than expected: " : "Machine-learning results: "}
              {ML.map((m) => `${m} ${per100(r99(m))}`).join(", ")} days in 100. When we checked if the gaps were real,
              GARCH was really better {tot.g} times and machine learning {tot.m} times. The other {tot.n} could be luck.
            </p>
            <Tech>99% breach rates; Diebold-Mariano tests on FZ0 at 95%, 5% level</Tech>
          </li>
          {gjr && (
            <li className="rounded-lg border border-warn-500 bg-warn-100 p-4" data-read>
              <div className="text-sm font-semibold text-warn-700">3 · Bad days come together</div>
              <p className="mt-1 text-lg">
                Only {pct(gjr.share_of_days_stress, 1)} of days were market-wide bad days. Yet they held{" "}
                {pct(gjr.share_of_breaches_on_stress_days, 1)} of the days GJR-t was beaten. Many stocks lose at once.
              </p>
              <Tech>Share of 99% breaches on stress days (Nifty 50 fell 2% or more)</Tech>
            </li>
          )}
        </ol>
      </Section>

      <Section title="How the study was done">
        <ol className="max-w-3xl list-decimal space-y-1 pl-6 text-lg" data-read>
          <li>We took {meta.data?.n_stocks ?? "the"} large Nifty 50 stocks with daily prices from 2015 to November 2026.</li>
          <li>The models learned from 2015 to 2021. We used 2022 and 2023 to make our choices.</li>
          <li>We then tested them on 2024 to 2026, days the models had never seen.</li>
          <li>Each evening, each model forecast the next day's likely worst loss.</li>
          <li>We counted how often real losses were bigger, and ran standard checks.</li>
        </ol>
      </Section>

      <Section title="Where to go next">
        <div className="flex flex-wrap gap-3 text-base" data-read>
          {[["/overview", "Results at a glance"], ["/models", "Compare the models"], ["/regimes", "Calm vs stressed days"],
            ["/stock", "Look at one stock"], ["/glossary", "What the words mean"]].map(([to, label]) => (
            <Link key={to} to={to} className="rounded border border-slate-800 px-3 py-1.5 font-semibold hover:bg-slate-800 hover:text-white">
              {label} →
            </Link>
          ))}
        </div>
      </Section>
    </>
  );
}
