import Figure, { type FigJson } from "../components/Figure";
import { ErrorBox, Loading, Section, Table } from "../components/ui";
import { Experts, Takeaway } from "../components/plain";
import { ML, ORDER, pct, useJson, type Meta } from "../lib/data";

interface BreachRow {
  model: string; alpha: number; total_breaches: number; share_of_breaches_on_stress_days: number; share_of_days_stress: number;
  max_breaches_one_day: number; days_with_10plus_breaches: number; top_days: string;
}

interface Range { feature: string; fit_window: string; fit_max_median: number; test_max_median: number }
interface Trace { name?: string; x?: string[]; y?: number[] }

export default function Regimes() {
  const b = useJson<Record<string, BreachRow[]>>("breach_summary.json");
  const fr = useJson<Range[]>("feature_ranges.json");
  const meta = useJson<Meta>("meta.json");
  const rows = b.data?.price.filter((r) => r.alpha === 0.01) || [];
  if (b.loading) return <Loading />;
  if (b.error || !rows.length) return <ErrorBox error={b.error || "missing breach summary"} />;
  const gjr = rows.find((r) => r.model === "GJR-t")!;
  const top = /^(\d{4}-\d{2}-\d{2}) (\d+) \(Nifty ([-\d.]+%)\)/.exec(gjr.top_days.split(";")[0].trim());
  const vix = fr.data?.find((r) => r.feature === "vix" && r.fit_window === "train_val");
  const allAbove = rows.every((r) => r.share_of_breaches_on_stress_days > r.share_of_days_stress);
  const n = meta.data?.n_stocks ?? 41;
  const q = (f: FigJson) => {
    const t = f.data as Trace[];
    const worse = t.every((s) => s.y && s.y[3] > s.y[0]);
    const best = [...t].sort((p, r) => (p.y?.[3] ?? 0) - (r.y?.[3] ?? 0))[0]?.name ?? "";
    return { worse, best };
  };
  return (
    <>
      <Takeaway>
        {allAbove
          ? "All models had their worst misses on days the whole market fell. No model avoided this."
          : "Some models had their worst misses on days the whole market fell."}
      </Takeaway>
      <Section title="What the market did">
        <Figure name="fig01_market_context" number="Figure 1"
          title="The models were judged on 2024 to 2026 (shaded), which includes the October 2026 rate rise"
          how="The black line shows how much the Nifty 50 grew since 2015. The amber line ranks the market fear gauge from 0 (calmest) to 100 (most fearful)."
          means={<>{vix && vix.test_max_median < vix.fit_max_median ? "In the test years, the fear gauge never reached the highs of earlier years. " : ""}
            {top ? `There were still sharp one-day falls, such as ${top[1]}, when the Nifty 50 fell ${top[3].replace("-", "")}.` : ""}</>}
          patch={(l) => ({
            yaxis: { ...(l.yaxis || {}), title: { text: "Nifty 50 growth since 2015 (%)" } },
            yaxis2: { ...(l.yaxis2 || {}), title: { text: "Market fear gauge rank (0–100)" } },
          })} />
      </Section>
      <Section title="Calm days versus fearful days">
        <Figure name="fig05_vix_quartiles_fz0" number="Figure 5"
          title={(f) => (q(f).worse ? "Every model found the most fearful days hardest to forecast" : "Scores on calm and fearful days")}
          how="We split the test days into four equal groups by the market fear gauge the day before. Each bar is a model's score in that group. Lower is better."
          means={(f) => {
            const best = q(f).best;
            return `On the most fearful quarter of days, the best score came from ${best}. ${ML.includes(best) ? "Machine learning did best on stressed days." : "Machine learning did not pull ahead when markets were stressed."}`;
          }}
          patch={() => ({
            xaxis: { title: { text: "Fear gauge the day before (calm → fearful)" } },
            yaxis: { title: { text: "Quality score (lower is better)" } },
          })} />
      </Section>
      <Section title="Do bad days come together?">
        <Figure name="fig13_breaches_by_day" number="Figure 13"
          title={top ? `On the worst day (${top[1]}), ${top[2]} of ${n} stocks lost more than the GJR-t forecast` : "Days on which many stocks lost more than forecast"}
          how={`Each bar counts how many of the ${n} stocks lost more than the forecast that day. Amber triangles mark market-wide bad days (the Nifty 50 fell 2% or more).`}
          means="Bad days hit many stocks at once. A fund that holds many of these stocks would take several losses on the same day. It should plan for that." />
        <Figure name="fig14_stress_share" number="Figure 14"
          title={`Market-wide bad days were ${pct(gjr.share_of_days_stress, 1)} of days but held ${pct(gjr.share_of_breaches_on_stress_days, 1)} of GJR-t's beaten days`}
          how="Each bar is the share of a model's beaten days that fell on market-wide bad days. The dashed line is what we would see if beaten days were spread evenly."
          means={allAbove
            ? "Every bar is far above the line. This is true for both kinds of model. Firms need an extra cushion for days when the whole market falls, whatever model they use."
            : "Not every bar is above the line."}
          patch={() => ({ yaxis: { title: { text: "Share of beaten days on market-wide bad days (%)" } } })} />
        <Experts title="breach clustering table (99% VaR, all stocks)">
        {rows.length > 0 && (
          <Table
            head={["Model", "Breaches (all stocks, 99%)", "Share on stress days", "Max stocks in one day", "Days with 10+ stocks", "Worst days"]}
            rows={ORDER.map((m) => rows.find((r) => r.model === m)!).map((r) => [
              r.model, r.total_breaches, pct(r.share_of_breaches_on_stress_days, 1), r.max_breaches_one_day,
              r.days_with_10plus_breaches, r.top_days,
            ])}
          />
        )}
        </Experts>
      </Section>
    </>
  );
}
