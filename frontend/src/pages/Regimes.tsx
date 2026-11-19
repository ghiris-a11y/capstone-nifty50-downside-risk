import Figure from "../components/Figure";
import { ErrorBox, Loading, Section, Table } from "../components/ui";
import { ORDER, pct, useJson } from "../lib/data";

interface BreachRow {
  model: string; alpha: number; total_breaches: number; share_of_breaches_on_stress_days: number; share_of_days_stress: number;
  max_breaches_one_day: number; days_with_10plus_breaches: number; top_days: string;
}

export default function Regimes() {
  const b = useJson<Record<string, BreachRow[]>>("breach_summary.json");
  const rows = b.data?.price.filter((r) => r.alpha === 0.01) || [];
  return (
    <>
      <Section title="Market context">
        <Figure name="fig01_market_context" number="Figure 1" />
      </Section>
      <Section title="Performance by India VIX regime">
        <Figure name="fig05_vix_quartiles_fz0" number="Figure 5" />
      </Section>
      <Section title="Breaches by day and market-stress days"
        note="A market-stress day is a day on which the Nifty 50 fell 2% or more (defined before the analysis). Breaches that arrive together across many stocks matter most for a portfolio, a broker or a clearing house.">
        <Figure name="fig13_breaches_by_day" number="Figure 13" />
        <Figure name="fig14_stress_share" number="Figure 14" />
        {b.loading && <Loading />}
        {b.error && <ErrorBox error={b.error} />}
        {rows.length > 0 && (
          <Table
            head={["Model", "Breaches (all stocks, 99%)", "Share on stress days", "Max stocks in one day", "Days with 10+ stocks", "Worst days"]}
            rows={ORDER.map((m) => rows.find((r) => r.model === m)!).map((r) => [
              r.model, r.total_breaches, pct(r.share_of_breaches_on_stress_days, 1), r.max_breaches_one_day,
              r.days_with_10plus_breaches, r.top_days,
            ])}
          />
        )}
      </Section>
    </>
  );
}
