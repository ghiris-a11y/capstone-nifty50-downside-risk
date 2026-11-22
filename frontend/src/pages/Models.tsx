import type { Layout } from "plotly.js";
import Figure, { isPhone } from "../components/Figure";
import BeatenChart from "../components/BeatenChart";
import { ErrorBox, Loading, Section, Table } from "../components/ui";
import { Experts, Takeaway } from "../components/plain";
import { dmTotals, GARCH, ML, ORDER, pct, rowAt, useJson, type BacktestRow, type DmCount, type SummaryFile } from "../lib/data";

export default function Models() {
  const dm = useJson<Record<string, Record<string, DmCount[]>>>("dm.json");
  const labels = useJson<SummaryFile>("summary.json");
  const bt = useJson<Record<string, BacktestRow[]>>("backtest.json");
  if (labels.loading || bt.loading || dm.loading) return <Loading />;
  if (!labels.data || !bt.data || !dm.data) return <ErrorBox error={labels.error || bt.error || dm.error || "missing data"} />;
  const rows = labels.data.summary.price;
  const b99 = bt.data.price.filter((r) => Math.abs(r.alpha - 0.01) < 1e-9);
  const nStocks = new Set(b99.map((r) => r.ticker)).size;
  const above = (m: string) => b99.filter((r) => r.model === m && r.exc_rate > 0.01).length;
  const share = (ms: string[], f: (r: BacktestRow) => boolean) => {
    const s = b99.filter((r) => ms.includes(r.model));
    return s.filter(f).length / s.length;
  };
  const bothPass = (r: BacktestRow) => r.kupiec_p > 0.05 && r.ind_p > 0.05;
  const tot = dmTotals(dm.data.price?.fz0_95);
  const es = (m: string) => rowAt(rows, m, 0.01).es_ratio;
  const esLow = ORDER.filter((m) => es(m) > 1);
  const x99 = rowAt(rows, "XGBoost", 0.01);
  const bestMedian = [...ORDER].sort((p, q) => rowAt(rows, p, 0.01).fz0_median_stocks - rowAt(rows, q, 0.01).fz0_median_stocks)[0];
  const ph = isPhone();
  // Two panels (19 in 20 and 99 in 100 days): on phones use short panel titles and show every model name, rotated.
  const twoPanel = (t: string) => (l: Partial<Layout>) => ({
    yaxis: { ...(l.yaxis || {}), title: { text: t } },
    ...(ph ? {
      annotations: (l.annotations || []).map((a) => ({ ...a, text: String(a.text).replace(" out of ", " in ") })),
      xaxis: { ...(l.xaxis || {}), tickangle: -90, dtick: 1 }, xaxis2: { ...((l as { xaxis2?: object }).xaxis2 || {}), tickangle: -90, dtick: 1 },
      margin: { ...(l.margin || {}), b: 130 },
    } : {}),
  });
  return (
    <>
      <Takeaway>
        {[...ORDER].sort((p, q) => Math.abs(rowAt(rows, p, 0.01).exc_rate - 0.01) - Math.abs(rowAt(rows, q, 0.01).exc_rate - 0.01))
          .slice(0, 3).every((m) => m.endsWith("-t"))
          ? "Classic models that allow for extreme days came closest to expected."
          : "The models closest to expected came from more than one type."}
        {tot.n > tot.g + tot.m ? " Most score gaps with machine learning could be luck." : ""}
      </Takeaway>
      <Section title="How often were the forecasts beaten?">
        <BeatenChart rows={rows} level="99" />
        <Figure name="fig04_exception_heatmap_99" number="Figure 4"
          phone={(f) => ({
            data: f.data.map((t) => ({ ...t, colorbar: { ...((t as { colorbar?: object }).colorbar || {}), orientation: "h", y: -0.2, yanchor: "top", thickness: 10, len: 0.9, title: { text: "Breach rate (%)", side: "top" } } })) as typeof f.data,
            layout: { ...f.layout, height: 1000, margin: { t: 40, l: 90, r: 10, b: 190 } },
          })}
          title={`GJR-t was beaten too often on ${above("GJR-t")} of ${nStocks} stocks; XGBoost on ${above("XGBoost")} of ${nStocks}`}
          how="Each square is one stock (row) and one model (column). Orange means beaten more than 1 day in 100; purple means fewer. Pale means close to ideal. Hover to see the number."
          means={`${pct(share(GARCH, (r) => r.exc_rate > 0.01), 0)} of the classic-model squares are above the ideal, against ${pct(share(ML, (r) => r.exc_rate > 0.01), 0)} for machine learning. A firm would need to watch those stocks more closely.`}
          patch={() => ({ xaxis: { title: { text: "Model" }, tickangle: isPhone() ? -60 : -35 } })} />
        <Figure name="fig07_kupiec_vs_christoffersen" number="Figure 7"
          title={`${pct(share(GARCH, bothPass), 0)} of classic-model results passed both checks, against ${pct(share(ML, bothPass), 0)} for machine learning`}
          how="Each dot is one stock and one model. Dots right of the dashed line passed “Did forecasts fail too often?”. Dots above the flat dashed line passed “Did failures come in clusters?”."
          means="A model that fails the first check sets aside the wrong amount of money. A model that fails the second check tends to fail several days in a row, which is when a firm can least afford it."
          patch={() => ({
            xaxis: { title: { text: ph ? "Fail too often? (right = pass)" : "Did forecasts fail too often? (right of line = pass)" }, range: [0, 1] },
            yaxis: { title: { text: ph ? "Clusters? (above = pass)" : "Did failures come in clusters? (above line = pass)" }, range: [0, 1] },
          })} />
        <Experts title="models ordered by breach rate (Figure 10) and the technical terms">
          <Figure name="fig10_leaderboard" number="Figure 10" />
        </Experts>
      </Section>

      <Section title="How big were the losses on the very bad days?">
        <Figure name="fig08_es_calibration" number="Figure 8"
          title={`On the very bad days, real losses were ${es("GJR-t").toFixed(2)} times the GJR-t forecast and ${es("XGBoost").toFixed(2)} times the XGBoost forecast`}
          how="Each box shows the spread across stocks. The dashed line at 1 is the ideal. Above 1 means the real loss was bigger than the forecast average."
          means={esLow.length
            ? `${esLow.length === ORDER.length ? "For every model" : `For ${esLow.length} of ${ORDER.length} models`}, the forecast of the loss on the very bad days was too small. A firm would have been surprised by the size of those losses.`
            : "No model's forecast of the average loss on the very bad days was too small on average."}
          patch={twoPanel("Real loss on bad days ÷ forecast (1 = exact)")} />
        <Figure name="fig11_fz0_mean_median" number="Figure 11"
          title={x99.fz0 - x99.fz0_median_stocks > 1
            ? "A few “no-risk” days made XGBoost's average score look much worse than its typical score"
            : "Average and typical scores tell the same story"}
          how="Lower is better. Open circles show the average. Filled circles show the typical stock. Values far off the scale are written as notes."
          means={`One forecast of “no risk” followed by a real loss can wreck an average, so we also show the typical stock. The best typical score at the 99 out of 100 level came from ${bestMedian}.`}
          patch={twoPanel(ph ? "Quality score (lower is better)" : "Overall forecast quality score (lower is better)")} />
      </Section>

      <Section title="Is the difference real, or just luck?">
        <Figure name="fig12_dm_summary" number="Figure 12"
          title={`GARCH was really better in ${tot.g} comparisons, machine learning in ${tot.m}; the other ${tot.n} could be luck`}
          how="Each bar is one machine-learning model, compared with each of the six GARCH models on every stock."
          means={tot.g > tot.m
            ? "Most gaps in the score are too small to be sure about. Where a gap is real, it almost always favours GARCH. The data give no reason to switch to machine learning for this job."
            : "Most gaps in the score are too small to be sure about."}
          patch={() => ({ xaxis: { title: { text: ph ? "Comparisons" : "Number of comparisons (stock × GARCH model)" } } })} />
        <Experts title="Diebold-Mariano counts for every input set and loss">
        <p className="mb-2 text-sm text-slate-600">Each ML model is compared with each of the six GARCH models for every stock (5% level). Counts are pairs: GARCH significantly lower loss / ML significantly lower loss / no significant difference.</p>
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
        </Experts>
      </Section>
    </>
  );
}
