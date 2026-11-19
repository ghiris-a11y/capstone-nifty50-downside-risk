import Figure from "../components/Figure";
import { ErrorBox, Loading, Section, Table } from "../components/ui";
import { ML, pct, useJson, type SummaryFile } from "../lib/data";

interface Variant { variant: string; contains: string; model: string; rel_pinball: number; exc99: number; calib_err: number; score: number }
interface Validation { selection: { created_utc: string; rule: string; selected_overall: string; selected_stationary: string }; variants: Variant[] }
interface Range { family: string; feature: string; fit_window: string; median_share_outside: number; fit_min_median: number; fit_max_median: number; test_min_median: number; test_max_median: number }

export default function Features() {
  const s = useJson<SummaryFile>("summary.json");
  const v = useJson<Validation>("validation.json");
  const r = useJson<Range[]>("feature_ranges.json");
  return (
    <>
      <Section title="What drives the XGBoost 99% VaR forecast">
        <Figure name="fig06_xgb_shap_importance" number="Figure 6" />
      </Section>

      <Section title="ML results by feature set (test window 2024-2026)"
        note="Each set is named by what it contains. GARCH and historical simulation do not use these features. Macro series (repo rate, CPI, IIP) are not yet included.">
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
    </>
  );
}
