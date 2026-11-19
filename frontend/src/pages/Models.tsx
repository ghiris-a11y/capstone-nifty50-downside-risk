import Figure from "../components/Figure";
import { ErrorBox, Loading, Section, Table } from "../components/ui";
import { useJson, type DmCount } from "../lib/data";

export default function Models() {
  const dm = useJson<Record<string, Record<string, DmCount[]>>>("dm.json");
  const labels = useJson<{ labels: Record<string, string> }>("summary.json");
  return (
    <>
      <Section title="Breach rates and backtests" note="Models are ordered by how close their 99% breach rate is to the nominal 1%. This is not a ranking of overall quality.">
        <Figure name="fig10_leaderboard" number="Figure 10" />
        <Figure name="fig04_exception_heatmap_99" number="Figure 4" />
        <Figure name="fig07_kupiec_vs_christoffersen" number="Figure 7" />
      </Section>
      <Section title="Expected Shortfall and joint VaR-ES loss">
        <Figure name="fig08_es_calibration" number="Figure 8" />
        <Figure name="fig11_fz0_mean_median" number="Figure 11" />
      </Section>
      <Section title="Diebold-Mariano tests"
        note="Each ML model is compared with each of the six GARCH models for every stock (5% level). Counts are pairs: GARCH significantly lower loss / ML significantly lower loss / no significant difference.">
        <Figure name="fig12_dm_summary" number="Figure 12" />
        {dm.loading && <Loading />}
        {dm.error && <ErrorBox error={dm.error} />}
        {dm.data && (
          <Table
            head={["Feature set", "ML model", "FZ0 95%", "Pinball 95%", "Pinball 99%"]}
            rows={Object.entries(dm.data).flatMap(([set, d]) =>
              d.fz0_95.map((r, i) => [
                labels.data?.labels[set] ?? set, r.model,
                `${r.garch} / ${r.ml} / ${r.none}`,
                `${d.pinball_95[i].garch} / ${d.pinball_95[i].ml} / ${d.pinball_95[i].none}`,
                `${d.pinball_99[i].garch} / ${d.pinball_99[i].ml} / ${d.pinball_99[i].none}`,
              ]))}
          />
        )}
      </Section>
    </>
  );
}
