import type { ReactNode } from "react";
import type { Data, Layout } from "plotly.js";
import Plot from "./Plot";
import { ErrorBox, Loading } from "./ui";
import { HowToRead, Means } from "./plain";
import { useJson } from "../lib/data";
import { plainText } from "../lib/plain";

export interface FigJson { data: Data[]; layout: Partial<Layout> }

type FromFig<T> = T | ((fig: FigJson) => T);
const resolve = <T,>(v: FromFig<T> | undefined, f: FigJson) => (typeof v === "function" ? (v as (f: FigJson) => T)(f) : v);

// Renders a figure exported by src/make_figures.py (the same figure as in the report). With `title` it becomes a
// plain-language chart: a finding as the title, a "How to read this" line, plain axis labels (`patch`) and a
// "What this means" box. The technical caption stays available under "Technical note".
export default function Figure({ name, number, title, how, means, patch }: {
  name: string; number?: string; title?: FromFig<string>; how?: ReactNode; means?: FromFig<ReactNode>;
  patch?: (layout: Partial<Layout>, fig: FigJson) => Partial<Layout>;
}) {
  const fig = useJson<FigJson>(`figures/${name}.json`);
  const captions = useJson<Record<string, string>>("figures/index.json");
  if (fig.loading) return <Loading what="chart" />;
  if (fig.error || !fig.data) return <ErrorBox error={fig.error || "missing figure"} />;
  const h = Math.min((fig.data.layout.height as number) || 560, 1000);
  const plain = title !== undefined;
  const data = plain ? fig.data.data.map((t) => ({ ...t, name: plainText((t as { name?: string }).name) })) as Data[] : fig.data.data;
  let layout: Partial<Layout> = { ...fig.data.layout, autosize: true, width: undefined, height: h };
  if (plain) {
    const ann = (layout.annotations || []).map((a) => ({ ...a, text: plainText(a.text) }));
    layout = { ...layout, title: undefined, annotations: ann, margin: { ...(layout.margin || {}), t: 40 } };
    if (patch) layout = { ...layout, ...patch(layout, fig.data) };
  }
  if (typeof window !== "undefined" && window.innerWidth < 640) // phone: smaller chart text so axis titles fit
    layout = { ...layout, font: { ...(layout.font || {}), size: 11 }, margin: { ...(layout.margin || {}), l: 55, r: 15 } };
  return (
    <figure className="mb-10 rounded-lg border border-slate-200 p-3">
      {plain && (
        <>
          <h3 className="mb-1 font-serif text-xl font-bold leading-snug" data-read>
            {number && <span className="text-slate-500">{number}. </span>}{resolve(title, fig.data)}
          </h3>
          {how && <HowToRead>{how}</HowToRead>}
        </>
      )}
      <Plot data={data} layout={layout} style={{ height: h }} />
      {plain && means && <Means>{resolve(means, fig.data)}</Means>}
      {captions.data?.[name] && (plain ? (
        <details className="mt-2 px-1 text-sm text-slate-600">
          <summary className="cursor-pointer">Technical note</summary>
          <p className="mt-1">{captions.data[name]}</p>
        </details>
      ) : (
        <figcaption className="px-2 pb-2 text-sm text-slate-600">
          {number && <span className="font-semibold">{number}. </span>}
          {captions.data[name]}
        </figcaption>
      ))}
    </figure>
  );
}
