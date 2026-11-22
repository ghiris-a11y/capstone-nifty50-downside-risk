import Figure, { type FigJson } from "../components/Figure";
import { ErrorBox, Loading, Section, Table } from "../components/ui";
import { Experts, HowToRead, Means, ModelName, Takeaway } from "../components/plain";
import { ML, pct, per100, rowAt, useJson, type SummaryFile } from "../lib/data";
import { FEATURE_PLAIN } from "../lib/plain";

interface Variant { variant: string; contains: string; model: string; rel_pinball: number; exc99: number; calib_err: number; score: number }
interface Validation { selection: { created_utc: string; rule: string; selected_overall: string; selected_stationary: string }; variants: Variant[] }
interface Range { family: string; feature: string; fit_window: string; median_share_outside: number; fit_min_median: number; fit_max_median: number; test_min_median: number; test_max_median: number }

export default function Features() {
  const s = useJson<SummaryFile>("summary.json");
  const v = useJson<Validation>("validation.json");
  const r = useJson<Range[]>("feature_ranges.json");
  if (s.loading) return <Loading />;
  if (!s.data) return <ErrorBox error={s.error || "missing summary"} />;
  const ex = (set: string, m: string) => rowAt(s.data!.summary[set], m, 0.01).exc_rate;
  const vixWorse = ML.every((m) => Math.abs(ex("price_vixlevel", m) - 0.01) > Math.abs(ex("price", m) - 0.01));
  const topFeature = (f: FigJson) => { const y = (f.data[0] as { y?: string[] }).y || []; return y[y.length - 1] ?? ""; };
  return (
    <>
      <Takeaway>
        {vixWorse
          ? "The market fear gauge moved XGBoost's forecasts the most. But adding it did not bring any model closer to expected."
          : "Extra market inputs changed the machine-learning forecasts, with mixed results."}
      </Takeaway>
      <Section title="What moves the machine-learning forecast?">
        <Figure name="fig06_xgb_shap_importance" number="Figure 6"
          title={(f) => `${FEATURE_PLAIN[topFeature(f)] ?? topFeature(f)} had the biggest effect on XGBoost's forecast`}
          how="Each bar shows how much one input moved XGBoost's forecast, on average. Longer bar = bigger effect. The thin line shows the uncertainty."
          means="A big effect is not the same as a better forecast. The next section checks whether these inputs made the forecasts more accurate."
          patch={(l, f) => {
            const y = (f.data[0] as { y?: string[] }).y || [];
            return {
              yaxis: { ...(l.yaxis || {}), title: { text: "Input" }, tickvals: y, ticktext: y.map((v) => FEATURE_PLAIN[v] ?? v) },
              xaxis: { ...(l.xaxis || {}), title: { text: "Average effect on the forecast (hundredths of 1% of return)" } },
              margin: { ...(l.margin || {}), l: 260, t: 40 },
            };
          }} />
      </Section>

      <Section title="Did extra market inputs help?">
        <HowToRead>
          Each card shows how many days in 100 a model was beaten. The ideal is 1. We compare price and volume only with the fear
          gauge added.
        </HowToRead>
        <div className="grid gap-3 sm:grid-cols-3" data-read>
          {ML.map((m) => (
            <div key={m} className="rounded border border-ml-100 bg-ml-50 p-3">
              <ModelName m={m} short />
              <p className="mt-1">Price and volume only: <b>{per100(ex("price", m))}</b> in 100</p>
              <p>With the fear gauge: <b>{per100(ex("price_vixlevel", m))}</b> in 100</p>
            </div>
          ))}
        </div>
        <Means>
          {vixWorse
            ? "With the fear gauge, every machine-learning model moved further from the ideal. The gauge helped a little in 2022 and 2023, but that gain mostly faded in the test years. The gauge also stayed well below the highs of the years the models learned from."
            : "The effect of the fear gauge was mixed across models."}
        </Means>
      </Section>

      <Experts title="ML results by input set, validation-window choice and feature ranges">
      <Section title="ML results by feature set (test window 2024-2026)"
        note="Each set is named by what it contains. GARCH and historical simulation do not use these features. The models use market data only; interest rates, price rises and factory output were left out on purpose.">
        {s.loading && <Loading />}
        {s.error && <ErrorBox error={s.error} />}
        {s.data && (
          <Table
            head={["Feature set", "Model", "Breach 95%", "Breach 99%", "Kupiec pass 99%", "Median FZ0 95%", "No-risk days 99%"]}
            rows={Object.keys(s.data.labels).flatMap((k) => ML.map((m) => {
              const at = (a: number) => s.data!.summary[k].find((x) => x.model === m && Math.abs(x.alpha - a) < 1e-9)!;
              return [s.data!.labels[k], m, pct(at(0.05).exc_rate), pct(at(0.01).exc_rate), pct(at(0.01).pass_kupiec, 0),
                at(0.05).fz0_median_stocks.toFixed(4), at(0.01).norisk_days];
            }))}
          />
        )}
      </Section>

      <Section title="Choosing feature sets on the validation window only"
        note="Models trained on 2015-2019, calibrated on 2020-2021 and evaluated on 2022-2023. The test window was not used for the choice. Score = pinball loss relative to the price-only set (below 1 = the features helped).">
        {v.data && (
          <>
            <p className="mb-3 text-sm text-slate-700">
              Rule: {v.data.selection.rule}. Recorded {v.data.selection.created_utc} UTC, before the test-window rerun.
              Selected overall: <b>{v.data.selection.selected_overall.replace("val_", "")}</b>; selected stationary variant:{" "}
              <b>{v.data.selection.selected_stationary.replace("val_", "")}</b>.
            </p>
            <Table
              head={["Variant", "Contains", "Model", "Pinball vs price", "Breach 99% (2022-23)", "Score"]}
              rows={v.data.variants.map((x) => [x.variant.replace("val_", ""), x.contains, x.model, x.rel_pinball.toFixed(3), pct(x.exc99), x.score.toFixed(4)])}
            />
          </>
        )}
      </Section>

      <Section title="Why market features behaved differently in the test window"
        note="Share of test days on which a feature lies outside the range of the data the final models were fitted on (2015-2023), median across stocks. Tree models cannot extrapolate beyond that range.">
        {r.data && (
          <Table
            head={["Feature", "Family", "Share of test days outside fitted range", "Fitted range", "Test range"]}
            rows={r.data.filter((x) => x.fit_window === "train_val" && x.family !== "price/volume").map((x) => [
              x.feature, x.family, pct(x.median_share_outside, 1),
              `${x.fit_min_median.toPrecision(3)} to ${x.fit_max_median.toPrecision(3)}`,
              `${x.test_min_median.toPrecision(3)} to ${x.test_max_median.toPrecision(3)}`,
            ])}
          />
        )}
      </Section>
      </Experts>
    </>
  );
}
