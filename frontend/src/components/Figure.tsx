import type { Data, Layout } from "plotly.js";
import Plot from "./Plot";
import { ErrorBox, Loading } from "./ui";
import { useJson } from "../lib/data";

interface FigJson { data: Data[]; layout: Partial<Layout> }

// Renders a figure exported by src/make_figures.py (the same figure as in the report), with its caption.
export default function Figure({ name, number }: { name: string; number?: string }) {
  const fig = useJson<FigJson>(`figures/${name}.json`);
  const captions = useJson<Record<string, string>>("figures/index.json");
  if (fig.loading) return <Loading what="chart" />;
  if (fig.error || !fig.data) return <ErrorBox error={fig.error || "missing figure"} />;
  const h = Math.min((fig.data.layout.height as number) || 560, 1000);
  return (
    <figure className="mb-8 rounded-lg border border-slate-200 p-2">
      <Plot data={fig.data.data} layout={{ ...fig.data.layout, autosize: true, width: undefined, height: h }} style={{ height: h }} />
      {captions.data?.[name] && (
        <figcaption className="px-2 pb-2 text-sm text-slate-600">
          {number && <span className="font-semibold">{number}. </span>}
          {captions.data[name]}
        </figcaption>
      )}
    </figure>
  );
}
