import { Link } from "react-router-dom";
import type { FigJson } from "../components/Figure";
import { ErrorBox, Kpi, Loading, Section } from "../components/ui";
import { Takeaway, Tech } from "../components/plain";
import { dmTotals, family, GARCH, ML, ORDER, per100, pct, rowAt, useJson, type BreachSummaryRow, type DmCount, type Meta, type SummaryFile } from "../lib/data";

interface Finding { head: string; text: string; tech?: string }
interface Action { who: string; act: string; why: string; tone: "garch" | "ml" | "warn" | "plain" }

// Median of each sector's per-stock average 99% VaR (in %) from the exported Figure 9 data, low to high.
function sectorMedians(f: FigJson): [string, number][] {
  return (f.data as { name?: string; y?: number[] }[]).filter((t) => t.y?.length).map((t) => {
    const y = [...(t.y as number[])].sort((p, q) => p - q);
    const mid = y.length % 2 ? y[(y.length - 1) / 2] : (y[y.length / 2 - 1] + y[y.length / 2]) / 2;
    return [t.name ?? "", mid] as [string, number];
  }).sort((p, q) => p[1] - q[1]);
}

export default function Start() {
  const s = useJson<SummaryFile>("summary.json");
  const dm = useJson<Record<string, Record<string, DmCount[]>>>("dm.json");
  const br = useJson<Record<string, BreachSummaryRow[]>>("breach_summary.json");
  const meta = useJson<Meta>("meta.json");
  const f9 = useJson<FigJson>("figures/fig09_sector_var.json");
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
  const vixRows = s.data.summary.price_vixlevel;
  const sec = f9.data ? sectorMedians(f9.data) : [];
  const top = gjr ? /^(\d{4}-\d{2}-\d{2}) (\d+)/.exec(gjr.top_days.split(";")[0].trim()) : null;
  const day = (iso: string) => new Date(iso + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  const actions: Action[] = [
    ...(garchClosest ? [{ who: "Bank risk desk", tone: "garch" as const,
      act: `Use ${closest[0]} or ${closest[1]} for 99 in 100 loss limits.`,
      why: `${closest[0]} was beaten on ${per100(r99(closest[0]))} days in 100, close to the ideal of 1. XGBoost was beaten on ${per100(r99("XGBoost"))}.` }] : []),
    ...(gjr ? [{ who: "Broker margin team", tone: "warn" as const,
      act: "Add an extra cushion on days the whole market falls.",
      why: `Those days were ${pct(gjr.share_of_days_stress, 1)} of all days but held ${pct(gjr.share_of_breaches_on_stress_days, 1)} of GJR-t's misses.${top ? ` On ${day(top[1])}, ${top[2]} stocks were beaten at once.` : ""}` }] : []),
    ...(sec.length ? [{ who: "Portfolio manager", tone: "plain" as const,
      act: "Set different limits for each sector.",
      why: `A typical ${sec[sec.length - 1][0]} stock needed about ${sec[sec.length - 1][1].toFixed(1)}% set aside for a bad day. ${sec[0][0]} needed about ${sec[0][1].toFixed(1)}%.` }] : []),
    ...(gjr ? [{ who: "Risk committee", tone: "plain" as const,
      act: "Count the misses every month. Look for days when many stocks miss together.",
      why: `GJR-t passed the check on both the number of misses and misses in a row for ${pct(at("GJR-t").pass_cc, 0)} of stocks. It still had ${gjr.days_with_10plus_breaches} days when 10 or more stocks missed at once.` }] : []),
    ...(vixRows ? [{ who: "Product or fintech team", tone: "ml" as const,
      act: "Do not pay for extra inputs before they prove their worth.",
      why: `Adding the fear gauge moved XGBoost from ${per100(r99("XGBoost"))} to ${per100(rowAt(vixRows, "XGBoost", 0.01).exc_rate)} days in 100. Interest rates were not tested.` }] : []),
  ];

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

      <Section title="What a firm should do">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {actions.map((a) => (
            <div key={a.who} className={`card flex flex-col p-5 ${a.tone === "garch" ? "border-t-4 border-t-garch-500" : a.tone === "ml" ? "border-t-4 border-t-ml-500" : a.tone === "warn" ? "border-t-4 border-t-warn-500" : "border-t-4 border-t-navy-900"}`} data-read>
              <div className="text-[13px] font-medium uppercase tracking-wide text-slate-500">For: {a.who}</div>
              <p className="mt-2 text-[17px] font-semibold leading-snug text-navy-900">{a.act}</p>
              <p className="mt-2 text-[15px] text-slate-600">{a.why}</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[13px] text-slate-500">These follow the report's recommendations chapter. All numbers come from the study's result files.</p>
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
            <Link key={to} to={to} className="inline-flex min-h-[40px] items-center rounded-full border border-navy-900 bg-white px-4 py-2 font-semibold text-navy-900 hover:bg-navy-900 hover:text-white">
              {label} →
            </Link>
          ))}
        </div>
      </Section>
    </>
  );
}
