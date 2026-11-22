import { Link } from "react-router-dom";
import { ErrorBox, Kpi, Loading, Section } from "../components/ui";
import { Takeaway, Tech } from "../components/plain";
import { dmTotals, family, GARCH, ML, ORDER, per100, pct, rowAt, useJson, type BreachSummaryRow, type DmCount, type Meta, type SummaryFile } from "../lib/data";

interface Finding { head: string; text: string; tech?: string }

export default function Start() {
  const s = useJson<SummaryFile>("summary.json");
  const dm = useJson<Record<string, Record<string, DmCount[]>>>("dm.json");
  const br = useJson<Record<string, BreachSummaryRow[]>>("breach_summary.json");
  const meta = useJson<Meta>("meta.json");
  if (s.loading || dm.loading || br.loading) return <Loading />;
  if (!s.data || !dm.data || !br.data) return <ErrorBox error={s.error || dm.error || br.error || "missing data"} />;

  const rows = s.data.summary.price;
  const at = (m: string) => rowAt(rows, m, 0.01);
  const r99 = (m: string) => at(m).exc_rate;
  const closest = [...ORDER].sort((a, b) => Math.abs(r99(a) - 0.01) - Math.abs(r99(b) - 0.01)).slice(0, 3);
  const garchClosest = closest.every((m) => GARCH.includes(m));
  const tot = dmTotals(dm.data.price?.fz0_95);
  const all = tot.g + tot.m + tot.n;
  const mlAllAbove = ML.every((m) => r99(m) > 0.01);
  const gjr = br.data.price.find((r) => r.model === "GJR-t" && r.alpha === 0.01);
  const bestG = [...GARCH].sort((a, b) => at(b).pass_kupiec - at(a).pass_kupiec)[0];
  const bestM = [...ML].sort((a, b) => at(b).pass_kupiec - at(a).pass_kupiec)[0];
  const esLow = ORDER.filter((m) => at(m).es_ratio > 1);
  const noRisk = at("XGBoost").norisk_days;

  const findings: Finding[] = [
    { head: "Closest to expected", text: `${closest.map((m) => `${m} (${per100(r99(m))})`).join(", ")} came closest to the ideal of 1 bad day in 100.${garchClosest ? " All three are classic models that allow for extreme days." : ""}`, tech: "99% VaR breach rate closest to nominal 1%" },
    { head: mlAllAbove ? "Machine learning did not do better" : "Machine learning was mixed", text: `The machine-learning models we tested were beaten on ${ML.map((m) => `${per100(r99(m))} (${m})`).join(", ")} days in 100.`, tech: "99% breach rates" },
    { head: tot.n > tot.g + tot.m ? "Most gaps could be luck" : "Many gaps were real", text: `GARCH was really better ${tot.g} times. Machine learning was really better ${tot.m} times. The other ${tot.n} could be luck.`, tech: "Diebold-Mariano tests on FZ0 at 95%, 5% level" },
    ...(gjr ? [{ head: "Bad days come together", text: `Only ${pct(gjr.share_of_days_stress, 1)} of days were market-wide bad days. Yet they held ${pct(gjr.share_of_breaches_on_stress_days, 1)} of the days GJR-t was beaten.`, tech: "Share of 99% breaches on stress days (Nifty 50 fell 2% or more)" }] : []),
    ...(esLow.length ? [{ head: "The very bad days were worse than forecast", text: `${esLow.length === ORDER.length ? "For every model" : `For ${esLow.length} of ${ORDER.length} models`}, the real loss on the very bad days was bigger than the forecast.`, tech: "Actual / forecast Expected Shortfall above 1" }] : []),
    ...(noRisk > 0 ? [{ head: "XGBoost sometimes saw no risk", text: `On ${noRisk} stock-days it forecast no loss at all. A small real loss on such a day counts as a miss.`, tech: "No-risk days: 99% forecast quantile at or above zero" }] : []),
  ];

  return (
    <>
      <Takeaway>
        {garchClosest
          ? "The classic statistics models stayed closest to the loss limits we expected. The machine-learning models did not do better."
          : "No single family of models stayed closest to the loss limits we expected."}
      </Takeaway>

      <Section title="Key numbers">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Kpi tone={family(closest[0]) === "GARCH" ? "garch" : family(closest[0]) === "ML" ? "ml" : undefined}
            caption="Closest to expected" value={<>{per100(r99(closest[0]))}<span className="ml-1 text-lg font-semibold tracking-normal text-slate-500">in 100</span></>}
            sub={`${closest[0]} was beaten on this many days in 100. The ideal is 1.`} />
          <Kpi tone="garch" caption="Passed the “too often?” check" value={pct(at(bestG).pass_kupiec, 0)}
            sub={`Share of stocks, ${bestG}. Best machine-learning model: ${bestM} ${pct(at(bestM).pass_kupiec, 0)}.`} />
          <Kpi caption="Gaps that could be luck" value={<>{tot.n}<span className="ml-1 text-lg font-semibold tracking-normal text-slate-500">of {all}</span></>}
            sub={`No real difference. GARCH really better ${tot.g}, machine learning ${tot.m}.`} />
          {gjr && (
            <Kpi tone="warn" caption="Misses on market-wide bad days" value={pct(gjr.share_of_breaches_on_stress_days, 1)}
              sub={`Of GJR-t's beaten days. These days were only ${pct(gjr.share_of_days_stress, 1)} of all days.`} />
          )}
        </div>
      </Section>

      <Section title="The question">
        <p className="card max-w-3xl p-5 text-[17px]" data-read>
          How much could a big Indian stock lose tomorrow? We compared two ways to forecast that loss. One uses classic
          statistics. The other uses machine learning.
        </p>
      </Section>

      <Section title="What we found">
        <ol className="card grid gap-x-10 gap-y-6 p-5 sm:p-6 md:grid-cols-2">
          {findings.map((f, i) => (
            <li key={f.head} className="flex gap-4" data-read>
              <span className="w-12 shrink-0 text-[34px] font-bold leading-none tracking-[-1px] text-slate-300" aria-hidden>
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <div className="text-[17px] font-semibold text-navy-900">{f.head}</div>
                <p className="mt-1 text-[15px] text-slate-600">{f.text}</p>
                {f.tech && <Tech>{f.tech}</Tech>}
              </div>
            </li>
          ))}
        </ol>
      </Section>

      <Section title="How the study was done">
        <ol className="card max-w-3xl list-decimal space-y-1 p-5 pl-10 text-[16px]" data-read>
          <li>We took {meta.data?.n_stocks ?? "the"} large Nifty 50 stocks with daily prices from 2015 to November 2026.</li>
          <li>The models learned from 2015 to 2021. We used 2022 and 2023 to make our choices.</li>
          <li>We then tested them on 2024 to 2026, days the models had never seen.</li>
          <li>Each evening, each model forecast the next day's likely worst loss.</li>
          <li>We counted how often real losses were bigger, and ran standard checks.</li>
        </ol>
      </Section>

      <Section title="Where to go next">
        <div className="flex flex-wrap gap-3 text-[15px]" data-read>
          {[["/overview", "Results at a glance"], ["/models", "Compare the models"], ["/regimes", "Calm vs stressed days"],
            ["/stock", "Look at one stock"], ["/glossary", "What the words mean"]].map(([to, label]) => (
            <Link key={to} to={to} className="rounded-full border border-navy-900 bg-white px-4 py-1.5 font-semibold text-navy-900 hover:bg-navy-900 hover:text-white">
              {label} →
            </Link>
          ))}
        </div>
      </Section>
    </>
  );
}
