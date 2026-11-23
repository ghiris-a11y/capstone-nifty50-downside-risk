import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import type { PlotParams } from "react-plotly.js";
import { Loading } from "./ui";

// Plotly is large, so it is downloaded only when the first chart is shown. Every chart on the site is a bar, box,
// scatter or heatmap chart, which the cartesian bundle covers (1.4 MB instead of 4.6 MB); the full bundle is loaded
// only for a chart that needs another type (the leaderboard table in a "For experts" section).
const CARTESIAN = new Set(["scatter", "scattergl", "bar", "box", "heatmap", "histogram", "line"]);
const LazyCartesian = lazy(async () => {
  const [{ default: Plotly }, { default: factory }] = await Promise.all([
    import("plotly.js-cartesian-dist-min"),
    import("react-plotly.js/factory"),
  ]);
  return { default: factory(Plotly) };
});
const LazyFull = lazy(async () => {
  const [{ default: Plotly }, { default: factory }] = await Promise.all([
    import("plotly.js-dist-min"),
    import("react-plotly.js/factory"),
  ]);
  return { default: factory(Plotly) };
});

// Draw a chart only when it comes near the screen: drawing every chart on a long tab at once blocked the page for
// a second or more, which is when clicks felt ignored.
export function useNearScreen<T extends Element>() {
  const ref = useRef<T>(null);
  const [near, setNear] = useState(typeof IntersectionObserver === "undefined");
  useEffect(() => {
    if (near || !ref.current) return;
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { setNear(true); io.disconnect(); } },
      { rootMargin: "600px 0px" });
    io.observe(ref.current);
    return () => io.disconnect();
  }, [near]);
  return [ref, near] as const;
}

// One hand-drawn-style note per chart: a thin curved arrow and an italic label pointing at a real data point.
// x and y are data values (dates allowed); y2 = use the right-hand axis. Without y the arrow points at the top of the plot.
export interface Annot { x: string | number; y?: number; y2?: boolean; text: string; short?: string }

interface Axis { _offset: number; _length: number; l2p: (v: number) => number; d2l: (v: unknown) => number }
interface Pos { px: number; py: number; lx: number; ly: number; anchor: "start" | "end"; w: number; h: number; text: string }

export default function Plot({ annotate, ...props }: PlotParams & { annotate?: Annot }) {
  const box = useRef<HTMLDivElement>(null);
  const [watch, near] = useNearScreen<HTMLDivElement>();
  const full = (props.data || []).some((d) => !CARTESIAN.has(String((d as { type?: string }).type ?? "scatter")));
  const LazyPlot = full ? LazyFull : LazyCartesian;
  const h = (props.style?.height as number) || (props.layout?.height as number) || 450;
  const [pos, setPos] = useState<Pos | null>(null);
  const place = useCallback((_: unknown, gd: HTMLElement) => {
    if (!annotate || !box.current) return;
    const fl = (gd as unknown as { _fullLayout: Record<string, Axis> })._fullLayout;
    const xa = fl.xaxis, ya = fl[annotate.y2 ? "yaxis2" : "yaxis"];
    if (!xa || !ya) return;
    const px = xa._offset + xa.l2p(xa.d2l(annotate.x));
    const py = annotate.y == null ? ya._offset + 8 : ya._offset + ya.l2p(ya.d2l(annotate.y));
    if (!Number.isFinite(px) || !Number.isFinite(py)) return;
    const w = box.current.clientWidth, h = box.current.clientHeight;
    // label goes up and to whichever side has more room; the curve bends from the label to the point
    const text = w < 480 && annotate.short ? annotate.short : annotate.text;
    const tw = text.length * 6.6;  // italic 13 px, approximate width
    let anchor: "start" | "end" = px > w / 2 ? "end" : "start";
    let lx = anchor === "end" ? px - 60 : px + 60;
    if (anchor === "end" && lx - tw < 4) lx = Math.min(tw + 4, w - 4);
    if (anchor === "start" && lx + tw > w - 4) { anchor = "end"; lx = Math.min(Math.max(px - 60, tw + 4), w - 4); }
    const ly = Math.max(py - 56, 16);
    setPos({ px, py, lx, ly, anchor, w, h, text });
  }, [annotate]);
  return (
    <div ref={watch} style={{ minHeight: near ? undefined : h }}>
    {near && <Suspense fallback={<div style={{ height: h }}><Loading what="chart" /></div>}>
      <div ref={box} className="relative">
        <LazyPlot
          useResizeHandler
          {...props}
          // no drag-to-zoom: on phones it captured the finger, so the page could not be scrolled over a chart
          layout={{ dragmode: false, ...(props.layout || {}) }}
          onInitialized={place}
          onUpdate={place}
          style={{ width: "100%", ...(props.style || {}) }}
          config={{ displaylogo: false, responsive: true, scrollZoom: false, displayModeBar: false, ...(props.config || {}) }}
        />
        {annotate && pos && (
          <svg className="pointer-events-none absolute left-0 top-0" width={pos.w} height={pos.h} aria-hidden>
            <defs>
              <marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M0 1L9 5L0 9" fill="none" stroke="#334155" strokeWidth="1.4" />
              </marker>
            </defs>
            <path d={`M ${pos.lx + (pos.anchor === "end" ? 6 : -6)} ${pos.ly - 4} Q ${pos.px} ${pos.ly - 4} ${pos.px} ${pos.py - 6}`}
              fill="none" stroke="#334155" strokeWidth="1.2" markerEnd="url(#arrowhead)" />
            <text x={pos.lx} y={pos.ly} textAnchor={pos.anchor} fontSize="13" fontStyle="italic" fill="#1f2937"
              style={{ paintOrder: "stroke", stroke: "white", strokeWidth: 4 }}>
              {pos.text}
            </text>
          </svg>
        )}
        {annotate && <span className="sr-only">{annotate.text}</span>}
      </div>
    </Suspense>}
    </div>
  );
}
