import type { ReactNode } from "react";
import type { Data, Layout } from "plotly.js";
import Plot, { type Annot } from "./Plot";
import { ErrorBox, Loading } from "./ui";
import { HowToRead, Means } from "./plain";
import { useJson } from "../lib/data";
import { plainText } from "../lib/plain";

export interface FigJson { data: Data[]; layout: Partial<Layout> }
export interface Big { value: ReactNode; text: ReactNode }

type FromFig<T> = T | ((fig: FigJson) => T);
const resolve = <T,>(v: FromFig<T> | undefined, f: FigJson) => (typeof v === "function" ? (v as (f: FigJson) => T)(f) : v);
export const isPhone = () => typeof window !== "undefined" && window.innerWidth <= 480;

// Chart typography for the dashboard: Inter, at least 11 px (phone) / 13 px (wider screens).
// Raise every font size in a figure (axis ticks, annotations, legends, trace text) to at least `min` px.
export function minFonts<T>(obj: T, min = 11): T {
  const walk = (v: unknown, key = ""): unknown => {
    if (Array.isArray(v)) return v.map((x) => walk(x, key));
    if (v && typeof v === "object") {
      const o: Record<string, unknown> = {};
      for (const [k, x] of Object.entries(v as Record<string, unknown>)) {
        o[k] = /font$/i.test(key) && k === "size" && typeof x === "number" ? Math.max(x, min) : walk(x, k);
      }
      return o;
    }
    return v;
  };
  return walk(obj) as T;
}

export function chartFont(layout: Partial<Layout>): Partial<Layout> {
  return { ...layout, font: { ...(layout.font || {}), family: "IBM Plex Sans, system-ui, sans-serif", size: isPhone() ? 11 : 13 } };
}

// Story layout shared by every chart: small grey label, bold title, "How to read this", an optional lead number,
// the chart with at most one annotation, an italic one-line takeaway, an optional column of big numbers (under the
// chart on phones), and the "What this means" box.
export function StoryCard({ label, title, how, lead, note, side, means, children, tech }: {
  label?: ReactNode; title?: ReactNode; how?: ReactNode; lead?: Big; note?: ReactNode; side?: Big[]; means?: ReactNode;
  children: ReactNode; tech?: ReactNode;
}) {
  return (
    <figure className="card mb-10 p-4 sm:p-6">
      {label && <div className="label text-[11.5px] text-slate-500">{label}</div>}
      {title && <h3 className="mt-1 text-[22px] font-bold leading-tight tracking-[-0.5px] text-navy-900 sm:text-[32px]" data-read>{title}</h3>}
      {how && <div className="mt-3"><HowToRead>{how}</HowToRead></div>}
      <div className={`mt-4 grid gap-6 ${side?.length ? "lg:grid-cols-[minmax(0,1fr)_230px]" : ""}`}>
        <div className="min-w-0">
          {lead && (
            <div className="mb-2" data-read>
              <div className="kpi text-navy-900">{lead.value}</div>
              <p className="mt-1 text-[13px] text-slate-500">{lead.text}</p>
            </div>
          )}
          {children}
          {note && <p className="mt-2 text-[15px] italic text-slate-600" data-read>{note}</p>}
        </div>
        {side?.length ? (
          <div>
            <div className="mb-5 h-1 w-12 rounded bg-slate-300" aria-hidden />
            <div className="grid grid-cols-2 gap-5 lg:grid-cols-1">
              {side.map((s, i) => (
                <div key={i} data-read>
                  <div className="display text-[34px] font-bold leading-none text-navy-900">{s.value}</div>
                  <p className="mt-1 text-[13px] leading-snug text-slate-600">{s.text}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
      {means && <Means>{means}</Means>}
      {tech}
    </figure>
  );
}

// Renders a figure exported by src/make_figures.py (the same figure as in the report). With `title` it becomes a
// plain-language chart: a finding as the title, a "How to read this" line, plain axis labels (`patch`) and a
// "What this means" box. The technical caption stays available under "Technical note".
export default function Figure({ name, number, title, how, means, patch, annotate, lead, note, side, phone }: {
  name: string; number?: string; title?: FromFig<string>; how?: ReactNode; means?: FromFig<ReactNode>;
  patch?: (layout: Partial<Layout>, fig: FigJson) => Partial<Layout>;
  annotate?: FromFig<Annot | undefined>; lead?: FromFig<Big | undefined>; note?: FromFig<ReactNode>; side?: FromFig<Big[] | undefined>;
  phone?: (fig: FigJson) => FigJson;  // phone-only layout (480 px and below); never changes the figure's numbers
}) {
  const fig = useJson<FigJson>(`figures/${name}.json`);
  const captions = useJson<Record<string, string>>("figures/index.json");
  if (fig.loading) return <Loading what="chart" />;
  if (fig.error || !fig.data) return <ErrorBox error={fig.error || "missing figure"} />;
  const shown = isPhone() && phone ? phone(fig.data) : fig.data;
  const h = Math.min((shown.layout.height as number) || 560, 1100);
  const plain = title !== undefined;
  const data = plain ? shown.data.map((t) => ({ ...t, name: plainText((t as { name?: string }).name) })) as Data[] : shown.data;
  let layout: Partial<Layout> = { ...shown.layout, autosize: true, width: undefined, height: h, paper_bgcolor: "#FFFDF8", plot_bgcolor: "#FFFDF8" };
  if (plain) {
    const ann = (layout.annotations || []).map((a) => ({ ...a, text: plainText(a.text) }));
    layout = { ...layout, title: undefined, annotations: ann, margin: { ...(layout.margin || {}), t: 40 } };
    if (patch) layout = { ...layout, ...patch(layout, fig.data) };
    // subplot titles sit just above the plot area: leave room so they stay inside the chart
    const top = (layout.annotations || []).some((a) => a.yref === "paper" && (a.y as number) >= 1 && a.yanchor === "bottom");
    if (top) layout = { ...layout, margin: { ...(layout.margin || {}), t: Math.max((layout.margin?.t as number) || 0, 64) } };
  }
  layout = chartFont(layout);
  if (isPhone()) layout = { ...layout, margin: { ...(layout.margin || {}), l: 55, r: 15 } };
  const tech = captions.data?.[name] ? (
    <details className="mt-3 text-sm text-slate-600">
      <summary className="flex min-h-[40px] cursor-pointer items-center">Technical note</summary>
      <p className="mt-1">{captions.data[name]}</p>
    </details>
  ) : undefined;
  const plot = <Plot data={minFonts(data)} layout={minFonts(layout)} style={{ height: h }} annotate={resolve(annotate, fig.data)} />;
  if (!plain) {
    return (
      <figure className="card mb-10 p-3">
        {plot}
        {captions.data?.[name] && (
          <figcaption className="px-2 pb-2 text-sm text-slate-600">
            {number && <span className="font-semibold">{number}. </span>}
            {captions.data[name]}
          </figcaption>
        )}
      </figure>
    );
  }
  return (
    <StoryCard label={number} title={resolve(title, fig.data)} how={how} lead={resolve(lead, fig.data)} note={resolve(note, fig.data)}
      side={resolve(side, fig.data)} means={resolve(means, fig.data)} tech={tech}>
      {plot}
    </StoryCard>
  );
}
