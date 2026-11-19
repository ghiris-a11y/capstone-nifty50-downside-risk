import Plot from "./Plot";
import { HowToRead, Means, ModelName, Status } from "./plain";
import { COLOURS, family, ORDER, per100, pct, rowAt, type SummaryRow } from "../lib/data";
import { IDEAL_TEXT, LEVEL_TEXT, status, STATUS_RULE } from "../lib/plain";

// Plain chart: how often each model's forecast was beaten, against the ideal value. Built from summary.json.
export default function BeatenChart({ rows, level }: { rows: SummaryRow[]; level: "99" | "95" }) {
  const a = level === "99" ? 0.01 : 0.05;
  const models = [...ORDER].sort((x, y) => Math.abs(rowAt(rows, x, a).exc_rate - a) - Math.abs(rowAt(rows, y, a).exc_rate - a));
  const vals = models.map((m) => 100 * rowAt(rows, m, a).exc_rate);
  const ico = { good: "✔", caution: "!", poor: "✖" } as const;
  const lv = models.map((m) => status(rowAt(rows, m, a).pass_kupiec));
  const best = models[0];
  const above = models.filter((m) => rowAt(rows, m, a).exc_rate > a);
  return (
    <figure className="mb-10 rounded-lg border border-slate-200 p-3">
      <h3 className="mb-1 font-serif text-xl font-bold leading-snug" data-read>
        {best} came closest to the ideal of {IDEAL_TEXT[level]} ({per100(rowAt(rows, best, a).exc_rate)} days in 100)
      </h3>
      <HowToRead>
        Each bar shows how many days in 100 the real loss was bigger than the forecast. The dashed line is the ideal. Bars to the
        right of it mean the model was beaten too often.
      </HowToRead>
      <Plot
        data={[{
          type: "bar", orientation: "h", y: models, x: vals, marker: { color: models.map((m) => COLOURS[m]) },
          text: vals.map((v, i) => `${v.toFixed(2)}  ${ico[lv[i]]} ${lv[i]}`), textposition: "outside", cliponaxis: false,
          hovertemplate: "%{y}: beaten on %{x:.2f} days in 100<extra></extra>",
        }]}
        layout={{
          autosize: true, height: 460, font: { family: "Times New Roman, serif", size: 15 }, margin: { t: 30, l: 120, r: 110, b: 60 },
          xaxis: { title: { text: `Days in 100 the forecast was beaten (likely worst loss, ${LEVEL_TEXT[level]})` }, rangemode: "tozero" },
          yaxis: { autorange: "reversed", ticksuffix: "  " }, showlegend: false,
          shapes: [{ type: "line", layer: "below", x0: 100 * a, x1: 100 * a, yref: "paper", y0: 0, y1: 1, line: { color: "#d18f00", dash: "dash", width: 3 } }],
          annotations: [{ x: 100 * a, yref: "paper", y: 1.06, text: `Ideal: ${IDEAL_TEXT[level]}`, showarrow: false, font: { color: "#8a5d00" } }],
        }}
        style={{ height: 460 }}
      />
      <p className="mt-1 text-sm text-slate-600">{STATUS_RULE}</p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        {models.map((m, i) => (
          <div key={m} className={`rounded border p-2 ${family(m) === "GARCH" ? "border-garch-100 bg-garch-50" : family(m) === "ML" ? "border-ml-100 bg-ml-50" : "border-slate-200"}`}>
            <ModelName m={m} short />
            <div className="mt-1 flex items-center justify-between gap-1 text-sm">
              <span>{vals[i].toFixed(2)} in 100</span><Status level={lv[i]} />
            </div>
            <div className="text-xs text-slate-500">{pct(rowAt(rows, m, a).pass_kupiec, 0)} of stocks passed</div>
          </div>
        ))}
      </div>
      <Means>
        {above.length === 0 ? "No model was beaten more often than the ideal." : <>
          {above.length} of {models.length} models were beaten too often. A firm using one of them would set too little money aside
          for the worst days. Models left of the line were a little too careful. They would tie up more money than needed.</>}
      </Means>
    </figure>
  );
}
